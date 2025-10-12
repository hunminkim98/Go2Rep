"""
GoPro camera adapters for Go2Rep v2.0

This module implements adapters for different GoPro models:
- GoPro11BleAdapter: BLE-based communication (GoPro 11)
- GoPro13CohnAdapter: COHN-based communication (GoPro 13)  
- MockCameraAdapter: Hardware-less simulation for testing
"""

import asyncio
import random
from typing import Sequence
from pathlib import Path

from .base import CameraAdapter, CameraInfo, CameraStatus


class MockCameraAdapter:
    """
    Mock camera adapter for hardware-less development and testing
    
    Simulates GoPro cameras with configurable behavior:
    - Fixed set of mock cameras
    - Configurable success/failure rates
    - Realistic timing delays
    """
    
    def __init__(self, 
                 mock_cameras: list[CameraInfo] | None = None,
                 success_rate: float = 0.9,
                 scan_delay: float = 2.0,
                 connect_delay: float = 3.0):
        """
        Initialize mock adapter
        
        Args:
            mock_cameras: List of mock cameras (default: 3 GoPro 11s)
            success_rate: Probability of successful operations (0.0-1.0)
            scan_delay: Delay for scan operations (seconds)
            connect_delay: Delay for connect operations (seconds)
        """
        self.success_rate = success_rate
        self.scan_delay = scan_delay
        self.connect_delay = connect_delay
        
        # Default mock cameras if none provided
        if mock_cameras is None:
            self.mock_cameras = [
                CameraInfo(
                    id="1234",
                    name="GoPro 1234", 
                    model="GP11",
                    status=CameraStatus.DISCONNECTED,
                    wifi_ssid="GP12345678",
                    wifi_password="gopro1234",
                    battery_level=85
                ),
                CameraInfo(
                    id="5678",
                    name="GoPro 5678",
                    model="GP11", 
                    status=CameraStatus.DISCONNECTED,
                    wifi_ssid="GP87654321",
                    wifi_password="gopro5678",
                    battery_level=72
                ),
                CameraInfo(
                    id="9012",
                    name="GoPro 9012",
                    model="GP13",
                    status=CameraStatus.DISCONNECTED,
                    wifi_ssid="GP13579246",
                    wifi_password="gopro9012", 
                    battery_level=95
                )
            ]
        else:
            self.mock_cameras = mock_cameras
    
    async def scan(self) -> Sequence[CameraInfo]:
        """Simulate camera scanning"""
        await asyncio.sleep(self.scan_delay)
        
        # Simulate occasional scan failures
        if random.random() > self.success_rate:
            raise RuntimeError("Mock scan failed - no cameras found")
        
        # Return copies with scanning status
        scanned_cameras = []
        for camera in self.mock_cameras:
            scanned_camera = CameraInfo(
                id=camera.id,
                name=camera.name,
                model=camera.model,
                status=CameraStatus.SCANNING,
                wifi_ssid=camera.wifi_ssid,
                wifi_password=camera.wifi_password,
                battery_level=camera.battery_level
            )
            scanned_cameras.append(scanned_camera)
        
        return scanned_cameras
    
    async def fetch_wifi_credentials(self, identifier: str) -> tuple[str, str]:
        """Simulate fetching WiFi credentials"""
        await asyncio.sleep(0.5)  # Quick operation
        
        # Find camera by identifier
        camera = next((c for c in self.mock_cameras if c.id == identifier), None)
        if not camera:
            raise ValueError(f"Mock camera {identifier} not found")
        
        return camera.wifi_ssid, camera.wifi_password
    
    async def enable_wifi(self, identifier: str) -> None:
        """Simulate enabling WiFi on camera"""
        await asyncio.sleep(1.0)
        
        # Simulate occasional WiFi enable failures
        if random.random() > self.success_rate:
            raise RuntimeError(f"Mock WiFi enable failed for camera {identifier}")
    
    async def connect_pc_to_wifi(self, ssid: str, password: str) -> bool:
        """Simulate PC WiFi connection"""
        await asyncio.sleep(self.connect_delay)
        
        # Simulate connection success/failure
        return random.random() <= self.success_rate


class GoPro11BleAdapter:
    """
    GoPro 11 BLE adapter wrapping existing tools
    
    Uses tools/Scan_for_GoPros.py and tools/Establish_Wifis.py
    """
    
    def __init__(self):
        """Initialize BLE adapter"""
        self._initialized = False
    
    def _ensure_initialized(self):
        """Ensure tutorial_modules are available"""
        if not self._initialized:
            try:
                # Import will fail if tutorial_modules not installed
                import tutorial_modules
                self._initialized = True
            except ImportError:
                raise RuntimeError(
                    "tutorial_modules not available. "
                    "Please install GoPro SDK or use MockCameraAdapter"
                )
    
    async def scan(self) -> Sequence[CameraInfo]:
        """Scan for GoPro 11 cameras via BLE"""
        self._ensure_initialized()
        
        # Import here to avoid dependency issues
        try:
            from tools.Scan_for_GoPros import scan_bluetooth_devices
        except ImportError:
            raise RuntimeError("tools.Scan_for_GoPros not available. Please ensure tools module is accessible.")
        
        try:
            devices = await scan_bluetooth_devices()
            cameras = []
            
            for device in devices:
                if device.name and "GoPro" in device.name:
                    # Extract identifier (last 4 digits)
                    identifier = device.name.split(" ")[-1] if " " in device.name else "0000"
                    
                    camera = CameraInfo(
                        id=identifier,
                        name=device.name,
                        model="GP11",
                        status=CameraStatus.DISCONNECTED
                    )
                    cameras.append(camera)
            
            return cameras
            
        except Exception as e:
            raise RuntimeError(f"BLE scan failed: {e}")
    
    async def fetch_wifi_credentials(self, identifier: str) -> tuple[str, str]:
        """Fetch WiFi credentials via BLE"""
        self._ensure_initialized()
        
        # Import here to avoid dependency issues  
        try:
            from tools.Establish_Wifis import connect_and_enable_wifi
        except ImportError:
            raise RuntimeError("tools.Establish_Wifis not available. Please ensure tools module is accessible.")
        
        try:
            ssid, password, client = await connect_and_enable_wifi(identifier=identifier)
            await client.disconnect()
            return ssid, password
            
        except Exception as e:
            raise RuntimeError(f"Failed to fetch WiFi credentials for {identifier}: {e}")
    
    async def enable_wifi(self, identifier: str) -> None:
        """Enable WiFi on GoPro 11"""
        # WiFi is enabled as part of fetch_wifi_credentials
        # This is a no-op for BLE adapter
        pass
    
    async def connect_pc_to_wifi(self, ssid: str, password: str) -> bool:
        """Connect PC to GoPro WiFi"""
        self._ensure_initialized()
        
        # Import here to avoid dependency issues
        try:
            from tools.Establish_Wifis import connect_to_wifi
        except ImportError:
            raise RuntimeError("tools.Establish_Wifis not available. Please ensure tools module is accessible.")
        
        try:
            success = connect_to_wifi(ssid, password)
            return bool(success)
            
        except Exception as e:
            raise RuntimeError(f"WiFi connection failed: {e}")


class GoPro13CohnAdapter:
    """
    GoPro 13 COHN adapter wrapping existing tools
    
    Uses tools/Establish_Wifis_GP13.py for COHN provisioning
    """
    
    def __init__(self):
        """Initialize COHN adapter"""
        self._initialized = False
    
    def _ensure_initialized(self):
        """Ensure tutorial_modules are available"""
        if not self._initialized:
            try:
                import tutorial_modules
                self._initialized = True
            except ImportError:
                raise RuntimeError(
                    "tutorial_modules not available. "
                    "Please install GoPro SDK or use MockCameraAdapter"
                )
    
    async def scan(self) -> Sequence[CameraInfo]:
        """Scan for GoPro 13 cameras via BLE"""
        self._ensure_initialized()
        
        # Import here to avoid dependency issues
        try:
            from tools.Establish_Wifis_GP13 import scan_bluetooth_devices
        except ImportError:
            raise RuntimeError("tools.Establish_Wifis_GP13 not available. Please ensure tools module is accessible.")
        
        try:
            devices = await scan_bluetooth_devices()
            cameras = []
            
            for device in devices:
                if device.name and "GoPro" in device.name:
                    # Extract identifier (last 4 digits)
                    identifier = device.name.split(" ")[-1] if " " in device.name else "0000"
                    
                    camera = CameraInfo(
                        id=identifier,
                        name=device.name,
                        model="GP13",
                        status=CameraStatus.DISCONNECTED
                    )
                    cameras.append(camera)
            
            return cameras
            
        except Exception as e:
            raise RuntimeError(f"COHN scan failed: {e}")
    
    async def fetch_wifi_credentials(self, identifier: str) -> tuple[str, str]:
        """Fetch WiFi credentials via COHN"""
        # COHN requires provisioning first - this is a placeholder
        # Full implementation would use tools/Establish_Wifis_GP13.py
        raise NotImplementedError(
            "COHN WiFi credentials require provisioning. "
            "Use provision_cohn() method instead."
        )
    
    async def enable_wifi(self, identifier: str) -> None:
        """Enable WiFi on GoPro 13"""
        # COHN doesn't require explicit WiFi enable
        pass
    
    async def connect_pc_to_wifi(self, ssid: str, password: str) -> bool:
        """Connect PC to GoPro WiFi"""
        # COHN uses different connection method
        raise NotImplementedError(
            "COHN connection requires different method. "
            "Use connect_to_access_point() instead."
        )
    
    async def provision_cohn(self, identifier: str, ssid: str, password: str) -> dict:
        """
        Provision COHN for GoPro 13
        
        Args:
            identifier: Camera identifier
            ssid: WiFi network SSID
            password: WiFi network password
            
        Returns:
            Dictionary with COHN credentials
        """
        self._ensure_initialized()
        
        # Import here to avoid dependency issues
        try:
            from tools.Establish_Wifis_GP13 import provision_one_gopro
        except ImportError:
            raise RuntimeError("tools.Establish_Wifis_GP13 not available. Please ensure tools module is accessible.")
        from pathlib import Path
        
        try:
            cert_dir = Path("./certifications")
            cert_dir.mkdir(exist_ok=True)
            
            creds = await provision_one_gopro(ssid, password, identifier, cert_dir)
            if creds:
                return {
                    "certificate": creds.certificate,
                    "username": creds.username, 
                    "password": creds.password,
                    "ip_address": creds.ip_address
                }
            else:
                raise RuntimeError(f"COHN provisioning failed for {identifier}")
                
        except Exception as e:
            raise RuntimeError(f"COHN provisioning failed: {e}")
