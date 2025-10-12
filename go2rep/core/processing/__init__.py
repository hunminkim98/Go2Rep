"""
Video processing modules for Go2Rep v2.0
"""

from .classifier import VideoClassifier
from .encoder import VideoEncoder, EncoderBackend

__all__ = [
    "VideoClassifier",
    "VideoEncoder", 
    "EncoderBackend"
]
