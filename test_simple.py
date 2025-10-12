#!/usr/bin/env python3
"""
Simple test for PerforMetrics v2.0

Tests basic functionality without GUI.
"""

import sys
import asyncio
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from go2rep.core.di import Container
from go2rep.core.models import CameraInfo, CameraStatus


async def test_basic_functionality():
    """Test basic functionality"""
    print("🚀 Testing PerforMetrics v2.0 Basic Functionality")
    print("=" * 50)
    
    # Create container
    container = Container(use_mock=True)
    
    # Test camera adapter
    camera_adapter = container.camera_adapter()
    print("✅ Camera adapter created")
    
    # Test state manager
    state_manager = container.state_manager()
    print("✅ State manager created")
    
    # Test camera scanning
    cameras = await camera_adapter.scan()
    print(f"✅ Camera scan completed: {len(cameras)} cameras found")
    
    for camera in cameras:
        print(f"   📹 {camera.id}: {camera.name}")
    
    # Test camera connection
    if cameras:
        camera_id = cameras[0].id
        print(f"🔌 Testing connection to {camera_id}...")
        
        success = await camera_adapter.connect(camera_id)
        if success:
            print("✅ Camera connection successful")
            
            # Test state manager
            state_manager.connect_camera(camera_id, cameras[0])
            connected = state_manager.get_connected_cameras()
            print(f"✅ State manager updated: {len(connected)} connected cameras")
            
            # Test disconnection
            success = await camera_adapter.disconnect(camera_id)
            if success:
                print("✅ Camera disconnection successful")
                state_manager.disconnect_camera(camera_id)
                connected = state_manager.get_connected_cameras()
                print(f"✅ State manager updated: {len(connected)} connected cameras")
            else:
                print("❌ Camera disconnection failed")
        else:
            print("❌ Camera connection failed")
    
    print("\n🎉 Basic functionality test completed!")


if __name__ == "__main__":
    asyncio.run(test_basic_functionality())
