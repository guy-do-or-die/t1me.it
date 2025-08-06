from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import Response, JSONResponse
from datetime import datetime
from ..config.settings import settings
from ..models.video import ScreenshotRequest, ScreenshotResponse
from ..services.screenshot import screenshot_service
from ..services.metadata import metadata_service
from ..services.storage import storage_service
from ..utils.validation import URLValidator
from ..utils.cache import CacheManager

router = APIRouter()


@router.get("/screenshot")
async def get_screenshot(
    url: str = Query(..., description="Video URL to capture screenshot from"),
    t: float = Query(0, description="Timestamp in seconds", ge=0),
    w: int = Query(1280, description="Screenshot width", ge=100, le=settings.MAX_WIDTH),
    h: int = Query(720, description="Screenshot height", ge=100, le=settings.MAX_HEIGHT)
):
    """Generate a screenshot from a video at the specified timestamp."""
    
    # Validate URL
    if not URLValidator.is_valid_video_url(url):
        raise HTTPException(status_code=400, detail="Invalid video URL")
    
    try:
        # Generate cache key
        cache_key = CacheManager.generate_cache_key(url, t, w, h)
        cache_filename = f"{cache_key}.jpg"
        
        # Check if screenshot already exists
        existing_screenshot = await storage_service.load_screenshot(cache_filename)
        if existing_screenshot:
            return Response(
                content=existing_screenshot,
                media_type="image/jpeg",
                headers={
                    "Cache-Control": f"public, max-age={settings.CACHE_EXPIRY}",
                    "Content-Disposition": f"inline; filename={cache_filename}"
                }
            )
        
        # Extract metadata
        metadata = await metadata_service.extract_video_metadata(url)
        
        # Capture screenshot
        screenshot_bytes = await screenshot_service.capture_video_screenshot(url, t, w, h)
        if not screenshot_bytes:
            raise HTTPException(status_code=500, detail="Failed to capture screenshot")
        
        # Process screenshot
        processed_bytes = await screenshot_service.process_screenshot(screenshot_bytes, w, h)
        
        # Save to cache
        await storage_service.save_screenshot(cache_filename, processed_bytes)
        
        return Response(
            content=processed_bytes,
            media_type="image/jpeg",
            headers={
                "Cache-Control": f"public, max-age={settings.CACHE_EXPIRY}",
                "Content-Disposition": f"inline; filename={cache_filename}"
            }
        )
        
    except Exception as e:
        print(f"Error generating screenshot: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate screenshot: {str(e)}")


@router.get("/cache/{cache_key}")
async def serve_cached_image(cache_key: str):
    """Serve a cached screenshot image."""
    
    # Add .jpg extension if not present
    if not cache_key.endswith('.jpg'):
        cache_key += '.jpg'
    
    screenshot_bytes = await storage_service.load_screenshot(cache_key)
    if not screenshot_bytes:
        raise HTTPException(status_code=404, detail="Image not found")
    
    return Response(
        content=screenshot_bytes,
        media_type="image/jpeg",
        headers={
            "Cache-Control": f"public, max-age={settings.CACHE_EXPIRY}",
            "Content-Disposition": f"inline; filename={cache_key}"
        }
    )


@router.delete("/cache/{cache_key}")
async def clear_cache_item(cache_key: str):
    """Clear a specific cached screenshot."""
    
    # Add .jpg extension if not present
    if not cache_key.endswith('.jpg'):
        cache_key += '.jpg'
    
    success = await storage_service.delete_screenshot(cache_key)
    if not success:
        raise HTTPException(status_code=404, detail="Cache item not found")
    
    return {"message": f"Cache item {cache_key} cleared successfully"}


@router.delete("/cache")
async def clear_all_cache():
    """Clear all cached screenshots."""
    
    deleted_count = await storage_service.clear_all_cache()
    
    return {
        "message": f"Cache cleared successfully",
        "deleted_files": deleted_count
    }
