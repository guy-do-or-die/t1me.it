import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application configuration settings."""
    
    # API Configuration
    TITLE: str = "t1me.it"
    DESCRIPTION: str = "Universal timecode-based video screenshot microservice"
    VERSION: str = "1.0.0"
    
    # Server Configuration
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))
       
    # Directory Configuration
    CACHE_DIR: Path = Path("cache")
    STATIC_DIR: Path = Path("static")
    LINKS_DIR: Path = Path("links")
    
    # Screenshot Configuration
    MAX_WIDTH: int = int(os.getenv("MAX_WIDTH", "1920"))
    MAX_HEIGHT: int = int(os.getenv("MAX_HEIGHT", "1080"))
    DEFAULT_WIDTH: int = 1280
    DEFAULT_HEIGHT: int = 720
    
    # Cache Configuration
    CACHE_EXPIRY: int = int(os.getenv("CACHE_EXPIRY", "86400"))  # 24 hours
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")
    
    # Browser Configuration
    BROWSER_TIMEOUT: int = int(os.getenv("BROWSER_TIMEOUT", "30000"))
    USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"

    @property
    def BASE_URL(self) -> str:
        """Get BASE_URL from environment or construct from HOST:PORT."""
        # Check for explicit BASE_URL override
        base_url = os.getenv("BASE_URL")
        if base_url:
            return base_url
            
        # Default to local development
        return f"http://{self.HOST}:{self.PORT}"
 
    def __init__(self):
        """Initialize settings and create required directories."""
        self.CACHE_DIR.mkdir(exist_ok=True)
        self.STATIC_DIR.mkdir(exist_ok=True)
        self.LINKS_DIR.mkdir(exist_ok=True)


# Global settings instance
settings = Settings()
