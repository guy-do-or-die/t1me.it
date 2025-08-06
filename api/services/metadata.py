from typing import Dict, Any
from urllib.parse import urlparse
from playwright.async_api import async_playwright
from ..config.settings import settings
from ..models.video import VideoMetadata


class MetadataService:
    """Service for extracting video metadata from web pages."""
    
    async def extract_video_metadata(self, url: str) -> VideoMetadata:
        """
        Extract video metadata using headless browser.
        
        Args:
            url: The video URL to extract metadata from
            
        Returns:
            VideoMetadata: Extracted metadata
        """
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    '--no-sandbox',
                    '--disable-setuid-sandbox',
                    '--disable-dev-shm-usage',
                    '--disable-accelerated-2d-canvas',
                    '--no-first-run',
                    '--no-zygote',
                    '--disable-gpu'
                ]
            )
            
            try:
                context = await browser.new_context(
                    user_agent=settings.USER_AGENT
                )
                
                page = await context.new_page()
                await page.goto(url, wait_until='networkidle', timeout=settings.BROWSER_TIMEOUT)
                
                # Extract metadata from the page
                title = await page.title() or "Video"
                
                # Try to get description from meta tags
                description = await self._extract_description(page)
                
                # Get site name
                site_name = await self._extract_site_name(page, url)
                
                # Try to get video duration (if available)
                duration = await self._extract_duration(page)
                
                # Try to get thumbnail URL
                thumbnail_url = await self._extract_thumbnail(page)
                
                return VideoMetadata(
                    title=title,
                    description=description,
                    site_name=site_name,
                    duration=duration,
                    thumbnail_url=thumbnail_url
                )
                
            finally:
                await browser.close()
    
    async def _extract_description(self, page) -> str:
        """Extract description from meta tags."""
        description = ""
        try:
            # Try standard description meta tag
            description_element = await page.query_selector('meta[name="description"]')
            if description_element:
                description = await description_element.get_attribute('content') or ""
            
            # Try og:description if no description found
            if not description:
                og_desc_element = await page.query_selector('meta[property="og:description"]')
                if og_desc_element:
                    description = await og_desc_element.get_attribute('content') or ""
            
            # Try twitter:description as fallback
            if not description:
                twitter_desc_element = await page.query_selector('meta[name="twitter:description"]')
                if twitter_desc_element:
                    description = await twitter_desc_element.get_attribute('content') or ""
                    
        except Exception:
            pass
        
        return description
    
    async def _extract_site_name(self, page, url: str) -> str:
        """Extract site name from meta tags or URL."""
        site_name = ""
        try:
            # Try og:site_name
            site_element = await page.query_selector('meta[property="og:site_name"]')
            if site_element:
                site_name = await site_element.get_attribute('content') or ""
            
            # Fallback to domain name
            if not site_name:
                parsed = urlparse(url)
                site_name = parsed.netloc
                if site_name.startswith('www.'):
                    site_name = site_name[4:]
                    
        except Exception:
            # Final fallback to domain from URL
            try:
                parsed = urlparse(url)
                site_name = parsed.netloc
            except Exception:
                site_name = "Unknown"
        
        return site_name
    
    async def _extract_duration(self, page) -> float:
        """Extract video duration if available."""
        try:
            # Try to find duration in various formats
            duration_selectors = [
                'meta[property="video:duration"]',
                'meta[name="duration"]',
                '[itemprop="duration"]'
            ]
            
            for selector in duration_selectors:
                element = await page.query_selector(selector)
                if element:
                    content = await element.get_attribute('content')
                    if content:
                        # Try to parse duration (could be in seconds or ISO 8601 format)
                        try:
                            return float(content)
                        except ValueError:
                            # Handle ISO 8601 duration format (PT1M30S)
                            if content.startswith('PT'):
                                return self._parse_iso_duration(content)
        except Exception:
            pass
        
        return None
    
    async def _extract_thumbnail(self, page) -> str:
        """Extract thumbnail URL from meta tags."""
        try:
            # Try og:image first
            og_image_element = await page.query_selector('meta[property="og:image"]')
            if og_image_element:
                thumbnail = await og_image_element.get_attribute('content')
                if thumbnail:
                    return thumbnail
            
            # Try twitter:image
            twitter_image_element = await page.query_selector('meta[name="twitter:image"]')
            if twitter_image_element:
                thumbnail = await twitter_image_element.get_attribute('content')
                if thumbnail:
                    return thumbnail
                    
        except Exception:
            pass
        
        return None
    
    def _parse_iso_duration(self, duration_str: str) -> float:
        """Parse ISO 8601 duration format (PT1M30S) to seconds."""
        try:
            import re
            # Remove PT prefix
            duration_str = duration_str[2:]
            
            # Extract hours, minutes, seconds
            hours = 0
            minutes = 0
            seconds = 0
            
            # Hours
            h_match = re.search(r'(\d+)H', duration_str)
            if h_match:
                hours = int(h_match.group(1))
            
            # Minutes
            m_match = re.search(r'(\d+)M', duration_str)
            if m_match:
                minutes = int(m_match.group(1))
            
            # Seconds
            s_match = re.search(r'(\d+(?:\.\d+)?)S', duration_str)
            if s_match:
                seconds = float(s_match.group(1))
            
            return hours * 3600 + minutes * 60 + seconds
            
        except Exception:
            return 0.0


# Global metadata service instance
metadata_service = MetadataService()
