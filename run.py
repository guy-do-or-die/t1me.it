#!/usr/bin/env python3
"""
Entry point for t1me.it - Universal timecode-based video screenshot microservice
"""

import uvicorn
from api.main import app
from api.config.settings import settings

if __name__ == "__main__":
    uvicorn.run(
        "api.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=True,  # Enable auto-reload during development
        log_level="info"
    )
