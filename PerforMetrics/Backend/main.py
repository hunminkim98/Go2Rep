"""
PerforMetrics Backend Server
FastAPI-based REST API for GoPro control and motion analysis
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sys
import os
from pathlib import Path

# Add GoPro module path
gopro_path = str(Path(__file__).parent.parent.parent / "GoPro")
if gopro_path not in sys.path:
    sys.path.insert(0, gopro_path)

from config import settings

# Import routers
from routers import gopro_ble, gopro_cohn

# Initialize FastAPI app
app = FastAPI(
    title="PerforMetrics API",
    description="REST API for multi-camera GoPro control and motion analysis",
    version=settings.API_VERSION,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(gopro_ble.router, prefix="/api/gopro/ble", tags=["GoPro BLE"])
app.include_router(gopro_cohn.router, prefix="/api/gopro/cohn", tags=["GoPro COHN"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "name": "PerforMetrics API",
        "version": settings.API_VERSION,
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return JSONResponse(
        status_code=200,
        content={
            "status": "healthy",
            "version": settings.API_VERSION,
            "workspace": settings.GOPRO_WORKSPACE_PATH
        }
    )


@app.get("/api/system/info")
async def system_info():
    """Get system information"""
    return {
        "workspace_path": settings.GOPRO_WORKSPACE_PATH,
        "gopro_module_available": os.path.exists(gopro_path),
        "python_version": sys.version,
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=True
    )

