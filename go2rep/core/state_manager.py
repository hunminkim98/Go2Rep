"""
Shared State Manager

Manages shared state between ViewModels for consistent data across views.
"""

from typing import Dict, List, Optional
from PySide6.QtCore import QObject, Signal
from .models import CameraInfo, CameraStatus


class StateManager(QObject):
    """
    Shared state manager for coordinating between ViewModels
    
    Manages:
    - Connected cameras
    - Recording cameras
    - Preview cameras
    - Global application state
    """
    
    # Signals for state changes
    camera_connected = Signal(str, CameraInfo)  # camera_id, camera_info
    camera_disconnected = Signal(str)  # camera_id
    camera_recording_started = Signal(str)  # camera_id
    camera_recording_stopped = Signal(str, str)  # camera_id, file_path
    camera_preview_started = Signal(str)  # camera_id
    camera_preview_stopped = Signal(str)  # camera_id
    
    def __init__(self):
        super().__init__()
        self._connected_cameras: Dict[str, CameraInfo] = {}
        self._recording_cameras: Dict[str, bool] = {}
        self._preview_cameras: Dict[str, bool] = {}
        
    def connect_camera(self, camera_id: str, camera_info: CameraInfo):
        """Connect a camera"""
        self._connected_cameras[camera_id] = camera_info
        self.camera_connected.emit(camera_id, camera_info)
        
    def disconnect_camera(self, camera_id: str):
        """Disconnect a camera"""
        if camera_id in self._connected_cameras:
            del self._connected_cameras[camera_id]
            
        # Stop any ongoing operations
        if camera_id in self._recording_cameras:
            del self._recording_cameras[camera_id]
        if camera_id in self._preview_cameras:
            del self._preview_cameras[camera_id]
            
        self.camera_disconnected.emit(camera_id)
        
    def start_recording(self, camera_id: str):
        """Start recording on camera"""
        if camera_id in self._connected_cameras:
            self._recording_cameras[camera_id] = True
            self.camera_recording_started.emit(camera_id)
            
    def stop_recording(self, camera_id: str, file_path: str):
        """Stop recording on camera"""
        if camera_id in self._recording_cameras:
            del self._recording_cameras[camera_id]
            self.camera_recording_stopped.emit(camera_id, file_path)
            
    def start_preview(self, camera_id: str):
        """Start preview on camera"""
        if camera_id in self._connected_cameras:
            self._preview_cameras[camera_id] = True
            self.camera_preview_started.emit(camera_id)
            
    def stop_preview(self, camera_id: str):
        """Stop preview on camera"""
        if camera_id in self._preview_cameras:
            del self._preview_cameras[camera_id]
            self.camera_preview_stopped.emit(camera_id)
            
    def get_connected_cameras(self) -> List[CameraInfo]:
        """Get list of connected cameras"""
        return list(self._connected_cameras.values())
        
    def get_connected_camera_ids(self) -> List[str]:
        """Get list of connected camera IDs"""
        return list(self._connected_cameras.keys())
        
    def is_camera_connected(self, camera_id: str) -> bool:
        """Check if camera is connected"""
        return camera_id in self._connected_cameras
        
    def is_camera_recording(self, camera_id: str) -> bool:
        """Check if camera is recording"""
        return camera_id in self._recording_cameras
        
    def is_camera_previewing(self, camera_id: str) -> bool:
        """Check if camera is previewing"""
        return camera_id in self._preview_cameras
        
    def get_camera_info(self, camera_id: str) -> Optional[CameraInfo]:
        """Get camera info by ID"""
        return self._connected_cameras.get(camera_id)
