"""
PerforMetrics Backend Configuration
"""
from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    API_HOST: str = "0.0.0.0"
    API_PORT: int = 8000
    API_VERSION: str = "1.0.0"
    
    # CORS Settings
    CORS_ORIGINS: List[str] = [
        "http://localhost",
        "http://localhost:5000",
        "http://127.0.0.1",
        "http://127.0.0.1:5000",
    ]
    
    # GoPro Settings
    GOPRO_WORKSPACE_PATH: str = "/Users/a/Desktop/Go2Rep"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

