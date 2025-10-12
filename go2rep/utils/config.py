"""
Configuration management for Go2Rep v2.0
"""

import os
from typing import Any, Dict, Optional
from pathlib import Path


class Config:
    """
    Application configuration manager.
    """
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize configuration.
        
        Args:
            config_file: Optional path to configuration file
        """
        self._config: Dict[str, Any] = {}
        self._load_defaults()
        
        if config_file and Path(config_file).exists():
            self._load_from_file(config_file)
    
    def _load_defaults(self):
        """Load default configuration values."""
        self._config = {
            # Application
            "APP_NAME": "Go2Rep",
            "APP_VERSION": "2.0.0-dev",
            "APP_ENV": os.getenv("GO2REP_ENV", "development"),
            
            # UI
            "UI_THEME": "glass",
            "UI_LANGUAGE": "en",
            "WINDOW_WIDTH": 1400,
            "WINDOW_HEIGHT": 900,
            
            # Camera
            "CAMERA_SCAN_TIMEOUT": 10.0,
            "CAMERA_CONNECT_TIMEOUT": 5.0,
            "CAMERA_RETRY_ATTEMPTS": 3,
            
            # Video Processing
            "VIDEO_OUTPUT_DIR": "output",
            "VIDEO_TEMP_DIR": "temp",
            "VIDEO_FORMAT": "mp4",
            "VIDEO_QUALITY": "high",
            
            # Analysis
            "POSE_MODEL": "rtmpose",
            "POSE_CONFIDENCE": 0.5,
            "POSE_SMOOTHING": True,
            
            # Logging
            "LOG_LEVEL": os.getenv("GO2REP_LOG_LEVEL", "INFO"),
            "LOG_FILE": "logs/go2rep.log",
            
            # Development
            "DEBUG_MODE": os.getenv("GO2REP_DEBUG", "false").lower() == "true",
            "MOCK_CAMERA": os.getenv("GO2REP_MOCK_CAMERA", "false").lower() == "true",
        }
    
    def _load_from_file(self, config_file: str):
        """Load configuration from file (placeholder for future implementation)."""
        # TODO: Implement configuration file loading (TOML/YAML)
        pass
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value.
        
        Args:
            key: Configuration key
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        return self._config.get(key, default)
    
    def set(self, key: str, value: Any):
        """
        Set configuration value.
        
        Args:
            key: Configuration key
            value: Configuration value
        """
        self._config[key] = value
    
    def update(self, config_dict: Dict[str, Any]):
        """
        Update configuration with dictionary.
        
        Args:
            config_dict: Dictionary of configuration values
        """
        self._config.update(config_dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Get configuration as dictionary.
        
        Returns:
            Configuration dictionary
        """
        return self._config.copy()