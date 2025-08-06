from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse, FileResponse
from pathlib import Path
from ..config.settings import settings

router = APIRouter()


@router.get("/")
async def root():
    """Serve the frontend interface."""
    return FileResponse("static/index.html")


@router.get("/{path:path}")
async def serve_frontend(path: str, request: Request):
    """Catch-all route to serve React frontend for client-side routing."""
    # Check if it's an API route - don't serve frontend for these
    if path.startswith(("api", "screenshot", "shorten", "s/", "cache", "health", "static")):
        # Let other routers handle these
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Not found")
    
    # For all other routes, serve the React app
    static_file = Path(f"static/{path}")
    if static_file.exists() and static_file.is_file():
        return FileResponse(static_file)
    
    # Default to index.html for React Router
    return FileResponse("static/index.html")


@router.get("/api")
async def api_info():
    """API endpoint with service information."""
    return {
        "service": settings.TITLE,
        "description": settings.DESCRIPTION,
        "version": settings.VERSION,
        "endpoints": {
            "screenshot": "/screenshot",
            "shorten": "/shorten",
            "resolve": "/s/{short_id}",
            "cache": "/cache/{cache_key}",
            "health": "/health"
        }
    }


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return JSONResponse(
        content={
            "status": "healthy",
            "service": settings.TITLE,
            "version": settings.VERSION
        }
    )
