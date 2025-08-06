import json
import aiofiles
from pathlib import Path
from typing import Optional, Dict, Any
import redis.asyncio as redis
from ..config.settings import settings


class StorageService:
    """Service for handling file and Redis storage operations."""
    
    def __init__(self):
        self.redis_client: Optional[redis.Redis] = None
    
    async def get_redis(self) -> Optional[redis.Redis]:
        """Get Redis client instance."""
        if self.redis_client is None:
            try:
                self.redis_client = redis.from_url(settings.REDIS_URL)
                await self.redis_client.ping()
            except Exception:
                self.redis_client = None
        return self.redis_client
    
    async def save_short_link(self, short_id: str, data: Dict[str, Any]) -> None:
        """
        Save short link data to file and optionally Redis.
        
        Args:
            short_id: The short link identifier
            data: The link data to save
        """
        # Save to file
        file_path = settings.LINKS_DIR / f"{short_id}.json"
        async with aiofiles.open(file_path, 'w') as f:
            await f.write(json.dumps(data, indent=2, default=str))
        
        # Save to Redis if available
        redis_client = await self.get_redis()
        if redis_client:
            try:
                await redis_client.setex(
                    f"link:{short_id}",
                    settings.CACHE_EXPIRY,
                    json.dumps(data, default=str)
                )
            except Exception:
                pass  # Fallback to file storage
    
    async def load_short_link(self, short_id: str) -> Optional[Dict[str, Any]]:
        """
        Load short link data from Redis or file.
        
        Args:
            short_id: The short link identifier
            
        Returns:
            Dict containing link data or None if not found
        """
        # Try Redis first
        redis_client = await self.get_redis()
        if redis_client:
            try:
                data = await redis_client.get(f"link:{short_id}")
                if data:
                    return json.loads(data)
            except Exception:
                pass
        
        # Fallback to file
        file_path = settings.LINKS_DIR / f"{short_id}.json"
        if file_path.exists():
            try:
                async with aiofiles.open(file_path, 'r') as f:
                    content = await f.read()
                    return json.loads(content)
            except Exception:
                pass
        
        return None
    
    async def save_screenshot(self, filename: str, image_bytes: bytes) -> Path:
        """
        Save screenshot to cache directory.
        
        Args:
            filename: The filename to save as
            image_bytes: The image data
            
        Returns:
            Path to the saved file
        """
        file_path = settings.CACHE_DIR / filename
        async with aiofiles.open(file_path, 'wb') as f:
            await f.write(image_bytes)
        return file_path
    
    async def load_screenshot(self, filename: str) -> Optional[bytes]:
        """
        Load screenshot from cache directory.
        
        Args:
            filename: The filename to load
            
        Returns:
            Image bytes or None if not found
        """
        file_path = settings.CACHE_DIR / filename
        if file_path.exists():
            try:
                async with aiofiles.open(file_path, 'rb') as f:
                    return await f.read()
            except Exception:
                pass
        return None
    
    async def delete_screenshot(self, filename: str) -> bool:
        """
        Delete screenshot from cache directory.
        
        Args:
            filename: The filename to delete
            
        Returns:
            True if deleted successfully, False otherwise
        """
        file_path = settings.CACHE_DIR / filename
        try:
            if file_path.exists():
                file_path.unlink()
                return True
        except Exception:
            pass
        return False
    
    async def clear_all_cache(self) -> int:
        """
        Clear all cached screenshots.
        
        Returns:
            Number of files deleted
        """
        deleted_count = 0
        try:
            for file_path in settings.CACHE_DIR.glob("*.jpg"):
                file_path.unlink()
                deleted_count += 1
        except Exception:
            pass
        return deleted_count


# Global storage service instance
storage_service = StorageService()
