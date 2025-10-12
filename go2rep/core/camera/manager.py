"""
Camera manager for Go2Rep v2.0

This module provides the main CameraManager class that orchestrates
camera operations using dependency injection and adapter pattern.
"""

import asyncio
from typing import Dict, List, Optional
from pathlib import Path

from .base import CameraAdapter, CameraInfo, CameraStatus
from .gopro import MockCameraAdapter, GoPro11BleAdapter, GoPro13CohnAdapter


class CameraManager:
    """
    Main camera management class
    
    Uses dependency injection to support different camera adapters
    and provides a unified interface for camera operations.
    """
    
    def __init__(self, 
                 adapters: Dict[str, CameraAdapter] | None = None,
                 prefer_mock: bool = False):
        """
        Initialize camera manager
        
        Args:
            adapters: Dictionary of adapter name -> adapter instance
            prefer_mock: If True, use mock adapter when available
        """
        self.prefer_mock = prefer_mock
        self.cameras: Dict[str, CameraInfo] = {}
        self._observers = []
        
        # Set up adapters
        if adapters is None:
            self.adapters = {
                "mock": MockCameraAdapter(),
                "gopro11": GoPro11BleAdapter(),
                "gopro13": GoPro13CohnAdapter()
            }
        else:
            self.adapters = adapters
    
    def add_observer(self, observer):
        """Add observer for camera state changes"""
        self._observers.append(observer)
    
    def remove_observer(self, observer):
        """Remove observer"""
        if observer in self._observers:
            self._observers.remove(observer)
    
    def notify_observers(self):
        """Notify all observers of camera state changes"""
        for observer in self._observers:
            if hasattr(observer, 'on_cameras_changed'):
                observer.on_cameras_changed(list(self.cameras.values()))
    
    async def scan(self, adapter_name: str | None = None) -> List[CameraInfo]:
        """
        Scan for cameras using specified adapter
        
        Args:
            adapter_name: Name of adapter to use (None = auto-select)
            
        Returns:
            List of discovered cameras
        """
        # Select adapter
        if adapter_name is None:
            adapter_name = self._select_adapter()
        
        if adapter_name not in self.adapters:
            raise ValueError(f"Unknown adapter: {adapter_name}")
        
        adapter = self.adapters[adapter_name]
        
        try:
            # Perform scan
            discovered_cameras = await adapter.scan()
            
            # Update internal state
            for camera in discovered_cameras:
                self.cameras[camera.id] = camera
            
            # Notify observers
            self.notify_observers()
            
            return discovered_cameras
            
        except Exception as e:
            # Update camera status to error
            for camera in self.cameras.values():
                camera.status = CameraStatus.ERROR
            
            self.notify_observers()
            raise RuntimeError(f"Camera scan failed: {e}")
    
    async def connect(self, camera_id: str, adapter_name: str | None = None) -> bool:
        """
        Connect to a specific camera
        
        Args:
            camera_id: Camera identifier
            adapter_name: Name of adapter to use (None = auto-select)
            
        Returns:
            True if connection successful
        """
        # Find camera
        if camera_id not in self.cameras:
            raise ValueError(f"Camera {camera_id} not found. Run scan() first.")
        
        camera = self.cameras[camera_id]
        
        # Select adapter based on camera model
        if adapter_name is None:
            adapter_name = self._select_adapter_for_camera(camera)
        
        if adapter_name not in self.adapters:
            raise ValueError(f"Unknown adapter: {adapter_name}")
        
        adapter = self.adapters[adapter_name]
        
        try:
            # Update status to scanning
            camera.status = CameraStatus.SCANNING
            self.notify_observers()
            
            # Get WiFi credentials
            ssid, password = await adapter.fetch_wifi_credentials(camera_id)
            camera.wifi_ssid = ssid
            camera.wifi_password = password
            
            # Enable WiFi on camera
            await adapter.enable_wifi(camera_id)
            
            # Connect PC to camera WiFi
            success = await adapter.connect_pc_to_wifi(ssid, password)
            
            if success:
                camera.status = CameraStatus.CONNECTED
            else:
                camera.status = CameraStatus.ERROR
            
            self.notify_observers()
            return success
            
        except Exception as e:
            camera.status = CameraStatus.ERROR
            self.notify_observers()
            raise RuntimeError(f"Camera connection failed: {e}")
    
    async def disconnect(self, camera_id: str) -> bool:
        """
        Disconnect from a camera
        
        Args:
            camera_id: Camera identifier
            
        Returns:
            True if disconnection successful
        """
        if camera_id not in self.cameras:
            return False
        
        camera = self.cameras[camera_id]
        camera.status = CameraStatus.DISCONNECTED
        camera.wifi_ssid = ""
        camera.wifi_password = ""
        
        self.notify_observers()
        return True
    
    async def get_battery_level(self, camera_id: str) -> int:
        """
        Get camera battery level
        
        Args:
            camera_id: Camera identifier
            
        Returns:
            Battery level (0-100)
        """
        if camera_id not in self.cameras:
            raise ValueError(f"Camera {camera_id} not found")
        
        camera = self.cameras[camera_id]
        
        # For mock adapter, return cached value
        if isinstance(self.adapters.get("mock"), MockCameraAdapter):
            return camera.battery_level
        
        # For real adapters, this would query the camera
        # For now, return cached value
        return camera.battery_level
    
    def get_cameras(self) -> List[CameraInfo]:
        """Get list of all known cameras"""
        return list(self.cameras.values())
    
    def get_camera(self, camera_id: str) -> Optional[CameraInfo]:
        """Get specific camera by ID"""
        return self.cameras.get(camera_id)
    
    def _select_adapter(self) -> str:
        """Select best available adapter"""
        if self.prefer_mock and "mock" in self.adapters:
            return "mock"
        
        # Prefer real adapters if available
        if "gopro11" in self.adapters:
            return "gopro11"
        elif "gopro13" in self.adapters:
            return "gopro13"
        elif "mock" in self.adapters:
            return "mock"
        
        raise RuntimeError("No camera adapters available")
    
    def _select_adapter_for_camera(self, camera: CameraInfo) -> str:
        """Select adapter based on camera model"""
        if camera.model == "GP11":
            return "gopro11"
        elif camera.model == "GP13":
            return "gopro13"
        else:
            # Fallback to mock for unknown models
            return "mock"
    
    async def provision_gopro13(self, camera_id: str, ssid: str, password: str) -> Dict:
        """
        Provision GoPro 13 for COHN
        
        Args:
            camera_id: Camera identifier
            ssid: WiFi network SSID
            password: WiFi network password
            
        Returns:
            Dictionary with COHN credentials
        """
        if camera_id not in self.cameras:
            raise ValueError(f"Camera {camera_id} not found")
        
        camera = self.cameras[camera_id]
        
        if camera.model != "GP13":
            raise ValueError(f"Camera {camera_id} is not GoPro 13")
        
        if "gopro13" not in self.adapters:
            raise RuntimeError("GoPro 13 adapter not available")
        
        adapter = self.adapters["gopro13"]
        
        try:
            # Update status
            camera.status = CameraStatus.SCANNING
            self.notify_observers()
            
            # Provision COHN
            creds = await adapter.provision_cohn(camera_id, ssid, password)
            
            # Update camera with COHN info
            camera.status = CameraStatus.CONNECTED
            self.notify_observers()
            
            return creds
            
        except Exception as e:
            camera.status = CameraStatus.ERROR
            self.notify_observers()
            raise RuntimeError(f"GoPro 13 provisioning failed: {e}")
