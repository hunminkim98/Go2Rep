"""
Mock Camera Adapter

Simulates camera operations for testing and development without hardware.
"""

import asyncio
import random
from typing import Dict, List
from ..di import CameraAdapter
from ..models import CameraInfo, CameraStatus


class MockCameraAdapter(CameraAdapter):
    """
    Mock implementation of CameraAdapter
    
    Simulates camera scanning, connection, and status management
    with realistic delays and state changes.
    """
    
    def __init__(self):
        self._cameras: Dict[str, CameraInfo] = {}
        self._connected_cameras: Dict[str, bool] = {}
        
    async def scan(self) -> List[CameraInfo]:
        """
        Scan for available cameras
        
        Returns a list of mock cameras with random properties.
        """
        # Simulate scan delay
        await asyncio.sleep(1.0)
        
        # Generate mock cameras
        mock_cameras = [
            CameraInfo(
                id="gopro_001",
                name="GoPro Hero 12",
                model="HERO12",
                status=CameraStatus.DISCONNECTED,
                battery_level=random.randint(20, 100),
                signal_strength=random.randint(60, 100),
                ip_address="192.168.1.101"
            ),
            CameraInfo(
                id="gopro_002", 
                name="GoPro Hero 11",
                model="HERO11",
                status=CameraStatus.DISCONNECTED,
                battery_level=random.randint(30, 90),
                signal_strength=random.randint(40, 80),
                ip_address="192.168.1.102"
            ),
            CameraInfo(
                id="gopro_003",
                name="GoPro Hero 10",
                model="HERO10", 
                status=CameraStatus.DISCONNECTED,
                battery_level=random.randint(10, 70),
                signal_strength=random.randint(30, 70),
                ip_address="192.168.1.103"
            )
        ]
        
        # Update internal state
        for camera in mock_cameras:
            self._cameras[camera.id] = camera
            self._connected_cameras[camera.id] = False
            
        return mock_cameras
        
    async def connect(self, camera_id: str) -> bool:
        """
        Connect to camera
        
        Simulates connection process with delay and status updates.
        """
        if camera_id not in self._cameras:
            return False
            
        # Simulate connection delay
        await asyncio.sleep(2.0)
        
        # Simulate occasional connection failure
        if random.random() < 0.1:  # 10% failure rate
            return False
            
        # Update status
        self._cameras[camera_id].status = CameraStatus.CONNECTED
        self._connected_cameras[camera_id] = True
        
        return True
        
    async def disconnect(self, camera_id: str) -> bool:
        """
        Disconnect from camera
        
        Simulates disconnection process.
        """
        if camera_id not in self._cameras:
            return False
            
        # Simulate disconnection delay
        await asyncio.sleep(0.5)
        
        # Update status
        self._cameras[camera_id].status = CameraStatus.DISCONNECTED
        self._connected_cameras[camera_id] = False
        
        return True
        
    async def get_status(self, camera_id: str) -> CameraStatus:
        """
        Get current camera status
        
        Returns the current status of the camera.
        """
        if camera_id not in self._cameras:
            return CameraStatus.ERROR
            
        return self._cameras[camera_id].status
        
    def get_camera_info(self, camera_id: str) -> CameraInfo:
        """Get camera information by ID"""
        return self._cameras.get(camera_id)
        
    def get_all_cameras(self) -> List[CameraInfo]:
        """Get all known cameras"""
        return list(self._cameras.values())
