#!/usr/bin/env python3
"""
Entry point for t1me.it - Universal timecode-based video screenshot microservice
"""

import os
import uvicorn
from api.main import app
from api.config.settings import settings

if __name__ == "__main__":
    # Detect if we're in development or production
    is_development = (
        os.getenv("ENVIRONMENT") == "development" or
        os.getenv("NODE_ENV") == "development" or
        os.getenv("RAILWAY_ENVIRONMENT") is None  # Not on Railway = local dev
    )
    
    print(f"Starting server in {'development' if is_development else 'production'} mode")
    
    uvicorn.run(
        "api.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=is_development,  # Enable reload only in development
        log_level="info"
    )
