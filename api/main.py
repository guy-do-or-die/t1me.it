from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from .config.settings import settings
from .routers import health, screenshots, links

# Get the project root directory (parent of api/)
PROJECT_ROOT = Path(__file__).parent.parent
STATIC_DIR = PROJECT_ROOT / "static"
ASSETS_DIR = STATIC_DIR / "assets"

# Create FastAPI application
app = FastAPI(
    title=settings.TITLE,
    description=settings.DESCRIPTION,
    version=settings.VERSION
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount static files - serve assets directly and static files
app.mount("/assets", StaticFiles(directory=str(ASSETS_DIR)), name="assets")
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Include routers - order matters! API routes first, then catch-all frontend route
app.include_router(screenshots.router, tags=["Screenshots"])
app.include_router(links.router, tags=["Links"])
app.include_router(health.router, tags=["Health"])  # Health router with catch-all must be last


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=settings.HOST, port=settings.PORT)
