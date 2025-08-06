from typing import Dict, Any, Optional
from pydantic import BaseModel, HttpUrl
from datetime import datetime


class VideoMetadata(BaseModel):
    """Video metadata extracted from the source page."""
    title: str
    description: Optional[str] = None
    site_name: Optional[str] = None
    duration: Optional[float] = None
    thumbnail_url: Optional[str] = None


class ScreenshotRequest(BaseModel):
    """Request model for screenshot generation."""
    url: HttpUrl
    timestamp: float = 0.0
    width: int = 1280
    height: int = 720


class ScreenshotResponse(BaseModel):
    """Response model for screenshot generation."""
    cache_key: str
    image_url: str
    width: int
    height: int
    timestamp: float
    metadata: VideoMetadata
    created_at: datetime
