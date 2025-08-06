from fastapi import APIRouter, HTTPException, Query, Request
from ..config.settings import settings
from ..models.link import ShortLinkRequest, ShortLinkResponse, ShortLinkInfo
from ..services.link import link_service
from ..utils.validation import URLValidator

router = APIRouter()


@router.post("/shorten")
async def create_short_link(
    url: str = Query(..., description="Video URL to shorten"),
    t: float = Query(0, description="Timestamp in seconds", ge=0),
    w: int = Query(1280, description="Screenshot width", ge=100, le=settings.MAX_WIDTH),
    h: int = Query(720, description="Screenshot height", ge=100, le=settings.MAX_HEIGHT)
) -> ShortLinkResponse:
    """Create a short link for a video URL with timestamp and custom screenshot."""
    
    # Validate URL
    if not URLValidator.is_valid_video_url(url):
        raise HTTPException(status_code=400, detail="Invalid video URL")
    
    try:
        request = ShortLinkRequest(
            url=url,
            timestamp=t,
            width=w,
            height=h
        )
        
        return await link_service.create_short_link(request)
        
    except Exception as e:
        print(f"Error creating short link: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to create short link: {str(e)}")


@router.get("/s/{short_id}")
async def resolve_short_link(short_id: str, request: Request):
    """Resolve short link - serve OpenGraph preview or redirect."""
    
    try:
        return await link_service.resolve_short_link(short_id, request)
    except Exception as e:
        print(f"Error resolving short link: {e}")
        raise HTTPException(status_code=404, detail="Short link not found")


@router.get("/s/{short_id}/info")
async def get_short_link_info(short_id: str) -> ShortLinkInfo:
    """Get information about a short link."""
    
    try:
        return await link_service.get_short_link_info(short_id)
    except Exception as e:
        print(f"Error getting short link info: {e}")
        raise HTTPException(status_code=404, detail="Short link not found")
