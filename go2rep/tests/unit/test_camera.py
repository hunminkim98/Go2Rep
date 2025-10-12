"""
Unit tests for camera management functionality
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from pathlib import Path

# Import core modules directly to avoid dependency issues
import sys
sys.path.insert(0, '/Users/a/Desktop/Go2Rep')

from go2rep.core.camera.base import CameraStatus, CameraInfo
from go2rep.core.camera.gopro import MockCameraAdapter, GoPro11BleAdapter, GoPro13CohnAdapter
from go2rep.core.camera.manager import CameraManager


class TestMockCameraAdapter:
    """Test MockCameraAdapter functionality"""
    
    def test_init_default(self):
        """Test default initialization"""
        adapter = MockCameraAdapter()
        assert len(adapter.mock_cameras) == 3
        assert adapter.success_rate == 0.9
        assert adapter.scan_delay == 2.0
        assert adapter.connect_delay == 3.0
    
    def test_init_custom(self):
        """Test custom initialization"""
        custom_cameras = [
            CameraInfo(id="9999", name="Test Camera", model="GP11")
        ]
        adapter = MockCameraAdapter(
            mock_cameras=custom_cameras,
            success_rate=0.5,
            scan_delay=1.0,
            connect_delay=2.0
        )
        assert len(adapter.mock_cameras) == 1
        assert adapter.success_rate == 0.5
        assert adapter.scan_delay == 1.0
        assert adapter.connect_delay == 2.0
    
    @pytest.mark.asyncio
    async def test_scan_success(self):
        """Test successful scan"""
        adapter = MockCameraAdapter(success_rate=1.0, scan_delay=0.1)
        
        cameras = await adapter.scan()
        
        assert len(cameras) == 3
        for camera in cameras:
            assert camera.status == CameraStatus.SCANNING
            assert camera.id in ["1234", "5678", "9012"]
    
    @pytest.mark.asyncio
    async def test_scan_failure(self):
        """Test scan failure"""
        adapter = MockCameraAdapter(success_rate=0.0, scan_delay=0.1)
        
        with pytest.raises(RuntimeError, match="Mock scan failed"):
            await adapter.scan()
    
    @pytest.mark.asyncio
    async def test_fetch_wifi_credentials(self):
        """Test WiFi credentials fetching"""
        adapter = MockCameraAdapter()
        
        ssid, password = await adapter.fetch_wifi_credentials("1234")
        
        assert ssid == "GP12345678"
        assert password == "gopro1234"
    
    @pytest.mark.asyncio
    async def test_fetch_wifi_credentials_invalid_id(self):
        """Test WiFi credentials with invalid ID"""
        adapter = MockCameraAdapter()
        
        with pytest.raises(ValueError, match="Mock camera 9999 not found"):
            await adapter.fetch_wifi_credentials("9999")
    
    @pytest.mark.asyncio
    async def test_enable_wifi_success(self):
        """Test successful WiFi enable"""
        adapter = MockCameraAdapter(success_rate=1.0)
        
        # Should not raise exception
        await adapter.enable_wifi("1234")
    
    @pytest.mark.asyncio
    async def test_enable_wifi_failure(self):
        """Test WiFi enable failure"""
        adapter = MockCameraAdapter(success_rate=0.0)
        
        with pytest.raises(RuntimeError, match="Mock WiFi enable failed"):
            await adapter.enable_wifi("1234")
    
    @pytest.mark.asyncio
    async def test_connect_pc_to_wifi_success(self):
        """Test successful PC WiFi connection"""
        adapter = MockCameraAdapter(success_rate=1.0, connect_delay=0.1)
        
        result = await adapter.connect_pc_to_wifi("test_ssid", "test_password")
        
        assert result is True
    
    @pytest.mark.asyncio
    async def test_connect_pc_to_wifi_failure(self):
        """Test PC WiFi connection failure"""
        adapter = MockCameraAdapter(success_rate=0.0, connect_delay=0.1)
        
        result = await adapter.connect_pc_to_wifi("test_ssid", "test_password")
        
        assert result is False


class TestGoPro11BleAdapter:
    """Test GoPro11BleAdapter functionality"""
    
    def test_init(self):
        """Test initialization"""
        adapter = GoPro11BleAdapter()
        assert not adapter._initialized
    
    def test_ensure_initialized_success(self):
        """Test successful initialization check"""
        adapter = GoPro11BleAdapter()
        
        with patch('tutorial_modules') as mock_module:
            adapter._ensure_initialized()
            assert adapter._initialized
    
    def test_ensure_initialized_failure(self):
        """Test initialization check failure"""
        adapter = GoPro11BleAdapter()
        
        with patch('builtins.__import__', side_effect=ImportError):
            with pytest.raises(RuntimeError, match="tutorial_modules not available"):
                adapter._ensure_initialized()
    
    @pytest.mark.asyncio
    async def test_scan_success(self):
        """Test successful BLE scan"""
        adapter = GoPro11BleAdapter()
        
        # Mock the scan function
        mock_device = Mock()
        mock_device.name = "GoPro 1234"
        
        with patch('tools.Scan_for_GoPros.scan_bluetooth_devices') as mock_scan:
            mock_scan.return_value = [mock_device]
            
            cameras = await adapter.scan()
            
            assert len(cameras) == 1
            assert cameras[0].id == "1234"
            assert cameras[0].name == "GoPro 1234"
            assert cameras[0].model == "GP11"
    
    @pytest.mark.asyncio
    async def test_scan_failure(self):
        """Test BLE scan failure"""
        adapter = GoPro11BleAdapter()
        
        with patch('tools.Scan_for_GoPros.scan_bluetooth_devices') as mock_scan:
            mock_scan.side_effect = Exception("BLE scan failed")
            
            with pytest.raises(RuntimeError, match="BLE scan failed"):
                await adapter.scan()
    
    @pytest.mark.asyncio
    async def test_fetch_wifi_credentials(self):
        """Test WiFi credentials fetching"""
        adapter = GoPro11BleAdapter()
        
        mock_client = AsyncMock()
        mock_client.disconnect = AsyncMock()
        
        with patch('tools.Establish_Wifis.connect_and_enable_wifi') as mock_connect:
            mock_connect.return_value = ("test_ssid", "test_password", mock_client)
            
            ssid, password = await adapter.fetch_wifi_credentials("1234")
            
            assert ssid == "test_ssid"
            assert password == "test_password"
            mock_client.disconnect.assert_called_once()


class TestGoPro13CohnAdapter:
    """Test GoPro13CohnAdapter functionality"""
    
    def test_init(self):
        """Test initialization"""
        adapter = GoPro13CohnAdapter()
        assert not adapter._initialized
    
    @pytest.mark.asyncio
    async def test_scan_success(self):
        """Test successful COHN scan"""
        adapter = GoPro13CohnAdapter()
        
        mock_device = Mock()
        mock_device.name = "GoPro 5678"
        
        with patch('tools.Establish_Wifis_GP13.scan_bluetooth_devices') as mock_scan:
            mock_scan.return_value = [mock_device]
            
            cameras = await adapter.scan()
            
            assert len(cameras) == 1
            assert cameras[0].id == "5678"
            assert cameras[0].name == "GoPro 5678"
            assert cameras[0].model == "GP13"
    
    @pytest.mark.asyncio
    async def test_fetch_wifi_credentials_not_implemented(self):
        """Test WiFi credentials fetching (not implemented)"""
        adapter = GoPro13CohnAdapter()
        
        with pytest.raises(NotImplementedError, match="COHN WiFi credentials require provisioning"):
            await adapter.fetch_wifi_credentials("5678")
    
    @pytest.mark.asyncio
    async def test_provision_cohn_success(self):
        """Test successful COHN provisioning"""
        adapter = GoPro13CohnAdapter()
        
        mock_creds = Mock()
        mock_creds.certificate = "test_cert"
        mock_creds.username = "test_user"
        mock_creds.password = "test_pass"
        mock_creds.ip_address = "192.168.1.100"
        
        with patch('tools.Establish_Wifis_GP13.provision_one_gopro') as mock_provision:
            mock_provision.return_value = mock_creds
            
            result = await adapter.provision_cohn("5678", "test_ssid", "test_password")
            
            assert result["certificate"] == "test_cert"
            assert result["username"] == "test_user"
            assert result["password"] == "test_pass"
            assert result["ip_address"] == "192.168.1.100"


class TestCameraManager:
    """Test CameraManager functionality"""
    
    def test_init_default(self):
        """Test default initialization"""
        manager = CameraManager()
        
        assert len(manager.adapters) == 3
        assert "mock" in manager.adapters
        assert "gopro11" in manager.adapters
        assert "gopro13" in manager.adapters
        assert manager.prefer_mock is False
    
    def test_init_custom(self):
        """Test custom initialization"""
        mock_adapter = MockCameraAdapter()
        custom_adapters = {"test": mock_adapter}
        
        manager = CameraManager(adapters=custom_adapters, prefer_mock=True)
        
        assert len(manager.adapters) == 1
        assert "test" in manager.adapters
        assert manager.prefer_mock is True
    
    def test_add_remove_observer(self):
        """Test observer management"""
        manager = CameraManager()
        observer = Mock()
        
        manager.add_observer(observer)
        assert observer in manager._observers
        
        manager.remove_observer(observer)
        assert observer not in manager._observers
    
    def test_notify_observers(self):
        """Test observer notification"""
        manager = CameraManager()
        observer = Mock()
        observer.on_cameras_changed = Mock()
        
        manager.add_observer(observer)
        manager.notify_observers()
        
        observer.on_cameras_changed.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_scan_mock_adapter(self):
        """Test scanning with mock adapter"""
        manager = CameraManager(prefer_mock=True)
        
        cameras = await manager.scan()
        
        assert len(cameras) == 3
        assert len(manager.cameras) == 3
    
    @pytest.mark.asyncio
    async def test_scan_specific_adapter(self):
        """Test scanning with specific adapter"""
        manager = CameraManager()
        
        cameras = await manager.scan("mock")
        
        assert len(cameras) == 3
    
    @pytest.mark.asyncio
    async def test_scan_invalid_adapter(self):
        """Test scanning with invalid adapter"""
        manager = CameraManager()
        
        with pytest.raises(ValueError, match="Unknown adapter: invalid"):
            await manager.scan("invalid")
    
    @pytest.mark.asyncio
    async def test_connect_success(self):
        """Test successful camera connection"""
        manager = CameraManager(prefer_mock=True)
        
        # First scan to populate cameras
        await manager.scan()
        
        # Connect to first camera
        result = await manager.connect("1234")
        
        assert result is True
        assert manager.cameras["1234"].status == CameraStatus.CONNECTED
    
    @pytest.mark.asyncio
    async def test_connect_camera_not_found(self):
        """Test connecting to non-existent camera"""
        manager = CameraManager()
        
        with pytest.raises(ValueError, match="Camera 9999 not found"):
            await manager.connect("9999")
    
    @pytest.mark.asyncio
    async def test_disconnect(self):
        """Test camera disconnection"""
        manager = CameraManager(prefer_mock=True)
        
        # First scan and connect
        await manager.scan()
        await manager.connect("1234")
        
        # Disconnect
        result = await manager.disconnect("1234")
        
        assert result is True
        assert manager.cameras["1234"].status == CameraStatus.DISCONNECTED
        assert manager.cameras["1234"].wifi_ssid == ""
    
    @pytest.mark.asyncio
    async def test_get_battery_level(self):
        """Test battery level retrieval"""
        manager = CameraManager(prefer_mock=True)
        
        await manager.scan()
        
        battery_level = await manager.get_battery_level("1234")
        
        assert battery_level == 85  # Mock camera battery level
    
    def test_get_cameras(self):
        """Test getting all cameras"""
        manager = CameraManager()
        
        # Add some cameras manually
        camera1 = CameraInfo(id="1234", name="Test 1", model="GP11")
        camera2 = CameraInfo(id="5678", name="Test 2", model="GP13")
        
        manager.cameras["1234"] = camera1
        manager.cameras["5678"] = camera2
        
        cameras = manager.get_cameras()
        
        assert len(cameras) == 2
        assert cameras[0].id in ["1234", "5678"]
    
    def test_get_camera(self):
        """Test getting specific camera"""
        manager = CameraManager()
        
        camera = CameraInfo(id="1234", name="Test", model="GP11")
        manager.cameras["1234"] = camera
        
        retrieved_camera = manager.get_camera("1234")
        assert retrieved_camera.id == "1234"
        
        non_existent = manager.get_camera("9999")
        assert non_existent is None
    
    def test_select_adapter(self):
        """Test adapter selection"""
        manager = CameraManager(prefer_mock=True)
        
        adapter_name = manager._select_adapter()
        assert adapter_name == "mock"
        
        manager.prefer_mock = False
        adapter_name = manager._select_adapter()
        assert adapter_name == "gopro11"
    
    def test_select_adapter_for_camera(self):
        """Test adapter selection for specific camera"""
        manager = CameraManager()
        
        gp11_camera = CameraInfo(id="1234", name="Test", model="GP11")
        gp13_camera = CameraInfo(id="5678", name="Test", model="GP13")
        unknown_camera = CameraInfo(id="9999", name="Test", model="UNKNOWN")
        
        assert manager._select_adapter_for_camera(gp11_camera) == "gopro11"
        assert manager._select_adapter_for_camera(gp13_camera) == "gopro13"
        assert manager._select_adapter_for_camera(unknown_camera) == "mock"
    
    @pytest.mark.asyncio
    async def test_provision_gopro13_success(self):
        """Test successful GoPro 13 provisioning"""
        manager = CameraManager()
        
        # Add GP13 camera
        gp13_camera = CameraInfo(id="5678", name="GoPro 5678", model="GP13")
        manager.cameras["5678"] = gp13_camera
        
        mock_creds = {
            "certificate": "test_cert",
            "username": "test_user",
            "password": "test_pass",
            "ip_address": "192.168.1.100"
        }
        
        with patch.object(manager.adapters["gopro13"], 'provision_cohn') as mock_provision:
            mock_provision.return_value = mock_creds
            
            result = await manager.provision_gopro13("5678", "test_ssid", "test_password")
            
            assert result == mock_creds
            assert manager.cameras["5678"].status == CameraStatus.CONNECTED
    
    @pytest.mark.asyncio
    async def test_provision_gopro13_wrong_model(self):
        """Test provisioning non-GP13 camera"""
        manager = CameraManager()
        
        # Add GP11 camera
        gp11_camera = CameraInfo(id="1234", name="GoPro 1234", model="GP11")
        manager.cameras["1234"] = gp11_camera
        
        with pytest.raises(ValueError, match="Camera 1234 is not GoPro 13"):
            await manager.provision_gopro13("1234", "test_ssid", "test_password")
