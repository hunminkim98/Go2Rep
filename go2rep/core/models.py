"""
Core data models for PerforMetrics v2.0

Contains data classes and enums used across the application.
"""

from dataclasses import dataclass
from enum import Enum


class CameraStatus(Enum):
    """Camera connection status"""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


@dataclass
class CameraInfo:
    """Camera information"""
    id: str
    name: str
    model: str
    status: CameraStatus
    battery_level: int = 0
    signal_strength: int = 0
    ip_address: str = "192.168.1.100"  # Default mock IP
