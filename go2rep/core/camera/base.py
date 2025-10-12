"""
Camera base types and protocols for Go2Rep v2.0

This module defines the core abstractions for camera management,
supporting both GoPro 11 (BLE) and GoPro 13 (COHN) protocols.
"""

from typing import Protocol, Sequence
from dataclasses import dataclass
from enum import Enum


class CameraStatus(Enum):
    """Camera connection status"""
    DISCONNECTED = "disconnected"
    SCANNING = "scanning"
    CONNECTED = "connected"
    RECORDING = "recording"
    ERROR = "error"


@dataclass
class CameraInfo:
    """Camera information container"""
    id: str        # GoPro identifier (last 4 digits)
    name: str      # Full device name (e.g., "GoPro 1234")
    model: str     # Model type ("GP11" or "GP13")
    status: CameraStatus = CameraStatus.DISCONNECTED
    wifi_ssid: str = ""
    wifi_password: str = ""
    battery_level: int = 0
    
    def __str__(self) -> str:
        return f"{self.name} ({self.model}) - {self.status.value}"


class CameraAdapter(Protocol):
    """
    Protocol for camera adapters
    
    This allows different implementations (BLE, COHN, Mock) 
    to be used interchangeably by CameraManager.
    """
    
    async def scan(self) -> Sequence[CameraInfo]:
        """
        Scan for available cameras
        
        Returns:
            List of discovered cameras
        """
        ...
    
    async def fetch_wifi_credentials(self, identifier: str) -> tuple[str, str]:
        """
        Get WiFi SSID and password from camera
        
        Args:
            identifier: Camera identifier (last 4 digits)
            
        Returns:
            Tuple of (ssid, password)
        """
        ...
    
    async def enable_wifi(self, identifier: str) -> None:
        """
        Enable WiFi on the camera
        
        Args:
            identifier: Camera identifier
        """
        ...
    
    async def connect_pc_to_wifi(self, ssid: str, password: str) -> bool:
        """
        Connect PC to camera's WiFi network
        
        Args:
            ssid: WiFi network name
            password: WiFi password
            
        Returns:
            True if connection successful
        """
        ...
