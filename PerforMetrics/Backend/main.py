"""
PerforMetrics Backend Server
FastAPI-based REST API for GoPro control and motion analysis
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import sys
import os
import time
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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

# Add request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    # Skip logging for health check endpoint to reduce noise
    skip_logging = request.url.path == "/health"
    
    start_time = time.time()
    if not skip_logging:
        logger.info(f"🔵 Incoming request: {request.method} {request.url.path}")
    
    response = await call_next(request)
    
    duration = time.time() - start_time
    if not skip_logging:
        logger.info(f"✅ Completed: {request.method} {request.url.path} - Status: {response.status_code} - Duration: {duration:.2f}s")
    
    return response

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

