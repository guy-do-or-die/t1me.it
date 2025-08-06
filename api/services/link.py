from typing import Optional
from datetime import datetime
from fastapi import Request
from fastapi.responses import HTMLResponse, RedirectResponse
from urllib.parse import urlparse
from ..config.settings import settings
from ..models.link import ShortLinkData, ShortLinkRequest, ShortLinkResponse, ShortLinkInfo
from ..models.video import VideoMetadata
from ..utils.cache import CacheManager
from ..services.storage import storage_service
from ..services.metadata import metadata_service
from ..services.screenshot import screenshot_service


class LinkService:
    """Service for managing short links and OpenGraph previews."""
    
    async def create_short_link(self, request: ShortLinkRequest) -> ShortLinkResponse:
        """
        Create a short link for a video URL with timestamp and custom screenshot.
        
        Args:
            request: Short link creation request
            
        Returns:
            ShortLinkResponse: Created short link information
        """
        url_str = str(request.url)
        
        # Extract video metadata
        metadata = await metadata_service.extract_video_metadata(url_str)
        
        # Generate screenshot for the thumbnail
        screenshot_bytes = await screenshot_service.capture_video_screenshot(
            url_str, request.timestamp, request.width, request.height
        )
        
        if not screenshot_bytes:
            raise Exception("Failed to capture screenshot")
        
        # Process screenshot
        processed_bytes = await screenshot_service.process_screenshot(
            screenshot_bytes, request.width, request.height
        )
        
        # Generate short ID
        short_id = CacheManager.generate_short_id()
        
        # Save screenshot
        screenshot_filename = f"{short_id}.jpg"
        await storage_service.save_screenshot(screenshot_filename, processed_bytes)
        
        # Create short link data
        link_data = ShortLinkData(
            short_id=short_id,
            original_url=url_str,
            timestamp=request.timestamp,
            width=request.width,
            height=request.height,
            screenshot_url=f"/cache/{screenshot_filename}",
            metadata=metadata,
            created_at=datetime.now(),
            clicks=0
        )
        
        # Save short link
        await storage_service.save_short_link(short_id, link_data.dict())
        
        # Return short link info
        short_url = f"{settings.BASE_URL}/s/{short_id}"
        return ShortLinkResponse(
            short_id=short_id,
            short_url=short_url,
            original_url=url_str,
            timestamp=request.timestamp,
            screenshot_url=f"{settings.BASE_URL}{link_data.screenshot_url}",
            metadata=metadata
        )
    
    async def resolve_short_link(self, short_id: str, request: Request):
        """
        Resolve short link - serve OpenGraph preview or redirect.
        
        Args:
            short_id: The short link identifier
            request: FastAPI request object
            
        Returns:
            HTMLResponse or RedirectResponse
        """
        # Load short link data
        link_data_dict = await storage_service.load_short_link(short_id)
        if not link_data_dict:
            raise Exception("Short link not found")
        
        # Convert to model
        link_data = ShortLinkData(**link_data_dict)
        
        # Increment click counter
        link_data.clicks += 1
        await storage_service.save_short_link(short_id, link_data.dict())
        
        # Check if request is from a bot/crawler (for OpenGraph) or preview is forced
        user_agent = request.headers.get("user-agent", "")
        force_preview = request.query_params.get("preview") == "1"
        
        # Debug: Print the user agent
        print(f"Short link access - User-Agent: {user_agent}")
        
        is_bot = force_preview or CacheManager.is_bot_user_agent(user_agent)
        
        print(f"Bot detection result: {is_bot} (force_preview: {force_preview})")
        
        if is_bot:
            # Serve OpenGraph HTML for social media previews
            return await self._serve_opengraph_preview(link_data, request)
        else:
            # Redirect to original URL with timestamp
            return self._redirect_to_original(link_data)
    
    async def get_short_link_info(self, short_id: str) -> ShortLinkInfo:
        """
        Get information about a short link.
        
        Args:
            short_id: The short link identifier
            
        Returns:
            ShortLinkInfo: Link information
        """
        link_data_dict = await storage_service.load_short_link(short_id)
        if not link_data_dict:
            raise Exception("Short link not found")
        
        link_data = ShortLinkData(**link_data_dict)
        
        return ShortLinkInfo(
            short_id=short_id,
            short_url=f"{settings.BASE_URL}/s/{short_id}",
            original_url=link_data.original_url,
            timestamp=link_data.timestamp,
            screenshot_url=f"{settings.BASE_URL}{link_data.screenshot_url}",
            metadata=link_data.metadata,
            created_at=link_data.created_at,
            clicks=link_data.clicks
        )
    
    async def _serve_opengraph_preview(self, link_data: ShortLinkData, request: Request) -> HTMLResponse:
        """Serve OpenGraph HTML preview with custom screenshot."""
        metadata = link_data.metadata
        
        # Add cache-busting parameter to force Facebook to refresh
        import time
        cache_buster = int(time.time())
        screenshot_url = f"{settings.BASE_URL}{link_data.screenshot_url}?v={cache_buster}"
        short_url = f"{settings.BASE_URL}/s/{link_data.short_id}"
        
        # Debug: Print the screenshot URL being used
        print(f"OpenGraph preview - screenshot_url: {screenshot_url}")
        print(f"DEBUG: og:image tag will be: <meta property='og:image' content='{screenshot_url}'>")
        
        # Build timestamp display
        timestamp = link_data.timestamp
        timestamp_display = ""
        if timestamp > 0:
            minutes = int(timestamp // 60)
            seconds = int(timestamp % 60)
            if minutes > 0:
                timestamp_display = f" at {minutes}:{seconds:02d}"
            else:
                timestamp_display = f" at 0:{seconds:02d}"
        
        title = f"{metadata.title}{timestamp_display}"
        description = metadata.description or f"Watch this video{timestamp_display}"
        
        html_content = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="utf-8">
    <title>{title}</title>
    <meta name="description" content="{description}">
    
    <!-- OpenGraph tags -->
    <meta property="og:title" content="{title}">
    <meta property="og:description" content="{description}">
    <meta property="og:image" content="{screenshot_url}">
    <meta property="og:image:secure_url" content="{screenshot_url}">
    <meta property="og:image:type" content="image/jpeg">
    <meta property="og:image:width" content="{link_data.width}">
    <meta property="og:image:height" content="{link_data.height}">
    <meta property="og:image:alt" content="Video screenshot at {timestamp_display}">
    <meta property="og:url" content="{short_url}">
    <meta property="og:type" content="article">
    <meta property="og:site_name" content="t1me.it">
    <meta property="article:author" content="t1me.it">
    <meta property="article:published_time" content="{link_data.created_at.isoformat()}">
    
    <!-- Additional meta tags to override YouTube -->
    <meta name="robots" content="index, follow">
    <meta name="thumbnail" content="{screenshot_url}">
    <link rel="image_src" href="{screenshot_url}">
    
    <!-- Twitter Card tags -->
    <meta name="twitter:card" content="summary_large_image">
    <meta name="twitter:title" content="{title}">
    <meta name="twitter:description" content="{description}">
    <meta name="twitter:image" content="{screenshot_url}">
    
    <!-- Auto-redirect disabled for bots to prevent OpenGraph conflicts -->
    
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
            text-align: center;
        }}
        .preview {{
            border: 1px solid #ddd;
            border-radius: 8px;
            padding: 20px;
            margin: 20px 0;
        }}
        .screenshot {{
            max-width: 100%;
            border-radius: 4px;
            margin: 10px 0;
        }}
        .redirect-link {{
            color: #1a73e8;
            text-decoration: none;
            font-weight: 500;
        }}
    </style>
</head>
<body>
    <h1>t1me.it</h1>
    <div class="preview">
        <h2>{title}</h2>
        <img src="{screenshot_url}" alt="Video screenshot" class="screenshot">
        <p>{description}</p>
        <p>
            <a href="{link_data.original_url}" class="redirect-link">
                Continue to {metadata.site_name} →
            </a>
        </p>
    </div>
    <p><small>Powered by t1me.it - Precise video screenshots, delivered instantly</small></p>
</body>
</html>
        """
        
        return HTMLResponse(content=html_content)
    
    def _redirect_to_original(self, link_data: ShortLinkData) -> RedirectResponse:
        """Redirect to original URL with timestamp."""
        original_url = link_data.original_url
        timestamp = link_data.timestamp
        
        # Add timestamp to URL if it's a supported platform
        if timestamp > 0:
            if "youtube.com" in original_url or "youtu.be" in original_url:
                separator = "&" if "?" in original_url else "?"
                original_url += f"{separator}t={int(timestamp)}s"
            elif "vimeo.com" in original_url:
                original_url += f"#t={int(timestamp)}s"
        
        return RedirectResponse(url=original_url, status_code=302)


# Global link service instance
link_service = LinkService()
