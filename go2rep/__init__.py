"""
Go2Rep v2.0 - Markerless Motion Capture Application

Modern PySide6-based application for GoPro-based motion capture workflows.
Replaces the monolithic Tkinter GUI with a modular MVVM architecture.
"""

__version__ = "2.0.0-dev"
__author__ = "Go2Rep Development Team"

# Import only core modules to avoid dependency conflicts
from .utils.logger import setup_logger, get_logger
from .utils.config import Config

__all__ = [
    "setup_logger",
    "get_logger", 
    "Config",
    "__version__",
    "__author__"
]
