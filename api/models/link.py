from typing import Dict, Any, Optional
from pydantic import BaseModel, HttpUrl
from datetime import datetime
from .video import VideoMetadata


class ShortLinkRequest(BaseModel):
    """Request model for creating short links."""
    url: HttpUrl
    timestamp: float = 0.0
    width: int = 1280
    height: int = 720


class ShortLinkData(BaseModel):
    """Internal model for short link data storage."""
    short_id: str
    original_url: str
    timestamp: float
    width: int
    height: int
    screenshot_url: str
    metadata: VideoMetadata
    created_at: datetime
    clicks: int = 0


class ShortLinkResponse(BaseModel):
    """Response model for short link creation."""
    short_id: str
    short_url: str
    original_url: str
    timestamp: float
    screenshot_url: str
    metadata: VideoMetadata


class ShortLinkInfo(BaseModel):
    """Response model for short link information."""
    short_id: str
    short_url: str
    original_url: str
    timestamp: float
    screenshot_url: str
    metadata: VideoMetadata
    created_at: datetime
    clicks: int
