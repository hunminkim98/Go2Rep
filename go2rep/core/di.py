"""
Dependency Injection Container

Simple DI container for managing dependencies between components.
Supports Mock/Real toggle for camera adapters.
"""

from typing import Protocol, TypeVar, Generic
from .models import CameraInfo, CameraStatus
from .state_manager import StateManager
from .download import DownloadAdapter


class CameraAdapter(Protocol):
    """Camera adapter interface"""
    
    async def scan(self) -> list[CameraInfo]:
        """Scan for available cameras"""
        ...
        
    async def connect(self, camera_id: str) -> bool:
        """Connect to camera"""
        ...
        
    async def disconnect(self, camera_id: str) -> bool:
        """Disconnect from camera"""
        ...
        
    async def get_status(self, camera_id: str) -> CameraStatus:
        """Get camera status"""
        ...


T = TypeVar('T')


class Container:
    """
    Simple dependency injection container
    
    Manages dependencies and provides Mock/Real toggle functionality.
    """
    
    def __init__(self, use_mock: bool = True, download_adapter_type: str = "mock"):
        self.use_mock = use_mock
        self.download_adapter_type = download_adapter_type
        self._instances = {}
        
        # Initialize shared state manager
        self._instances['state_manager'] = StateManager()
        
    def camera_adapter(self) -> CameraAdapter:
        """Get camera adapter (Mock or Real based on toggle)"""
        if 'camera_adapter' not in self._instances:
            if self.use_mock:
                from .camera.mock_adapter import MockCameraAdapter
                self._instances['camera_adapter'] = MockCameraAdapter()
            else:
                # TODO: Implement RealCameraAdapter when needed
                from .camera.mock_adapter import MockCameraAdapter
                self._instances['camera_adapter'] = MockCameraAdapter()
                
        return self._instances['camera_adapter']
        
    def download_adapter(self) -> DownloadAdapter:
        """Get download adapter (Mock, Legacy, or GP13 based on toggle)"""
        if 'download_adapter' not in self._instances:
            from .download import create_download_adapter
            self._instances['download_adapter'] = create_download_adapter(self.download_adapter_type)
                
        return self._instances['download_adapter']
        
    def state_manager(self) -> StateManager:
        """Get shared state manager"""
        return self._instances['state_manager']
        
    def get(self, dependency_type: type[T]) -> T:
        """Generic dependency getter"""
        if dependency_type == CameraAdapter:
            return self.camera_adapter()
        elif dependency_type == DownloadAdapter:
            return self.download_adapter()
        raise ValueError(f"Unknown dependency type: {dependency_type}")
        
    def set_mock_mode(self, use_mock: bool):
        """Toggle between Mock and Real adapters"""
        self.use_mock = use_mock
        # Clear cached instances to force recreation
        self._instances.clear()
        
    def set_download_adapter_type(self, adapter_type: str):
        """Set download adapter type (mock, legacy, gp13)"""
        self.download_adapter_type = adapter_type
        # Clear cached download adapter to force recreation
        if 'download_adapter' in self._instances:
            del self._instances['download_adapter']
