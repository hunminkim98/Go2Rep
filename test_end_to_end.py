#!/usr/bin/env python3
"""
End-to-End Test Script for PerforMetrics v2.0

Tests the complete workflow from camera scanning to recording.
"""

import sys
import asyncio
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from PySide6.QtWidgets import QApplication
from qasync import QEventLoop

from go2rep.core.di import Container
from go2rep.core.state_manager import StateManager
from go2rep.core.models import CameraInfo, CameraStatus
from go2rep.ui.viewmodels.camera_vm import CameraViewModel
from go2rep.ui.viewmodels.capture_vm import CaptureViewModel


class EndToEndTester:
    """End-to-end test runner"""
    
    def __init__(self):
        self.container = Container(use_mock=True)
        self.state_manager = self.container.state_manager()
        self.camera_adapter = self.container.camera_adapter()
        
        # Create ViewModels
        self.camera_vm = CameraViewModel(self.camera_adapter, self.state_manager)
        self.capture_vm = CaptureViewModel(self.camera_adapter, self.state_manager)
        
        # Test results
        self.test_results = {}
        
    async def run_all_tests(self):
        """Run all end-to-end tests"""
        print("🚀 Starting PerforMetrics v2.0 End-to-End Tests")
        print("=" * 60)
        
        # Test 1: Camera Scanning
        await self.test_camera_scanning()
        
        # Test 2: Camera Connection
        await self.test_camera_connection()
        
        # Test 3: State Synchronization
        await self.test_state_synchronization()
        
        # Test 4: Recording Workflow
        await self.test_recording_workflow()
        
        # Test 5: Preview Workflow
        await self.test_preview_workflow()
        
        # Test 6: Error Handling
        await self.test_error_handling()
        
        # Print results
        self.print_test_results()
        
    async def test_camera_scanning(self):
        """Test camera scanning functionality"""
        print("\n📷 Test 1: Camera Scanning")
        print("-" * 30)
        
        try:
            # Start scanning
            await self.camera_vm.scan()
            
            # Wait for completion
            await asyncio.sleep(2)
            
            # Check results
            cameras = self.camera_vm.get_all_cameras()
            
            if len(cameras) == 3:
                print("✅ PASS: Found 3 mock cameras")
                self.test_results["camera_scanning"] = True
            else:
                print(f"❌ FAIL: Expected 3 cameras, got {len(cameras)}")
                self.test_results["camera_scanning"] = False
                
            # Print camera details
            for camera in cameras:
                print(f"   📹 {camera.id}: {camera.name} ({camera.status.value})")
                
        except Exception as e:
            print(f"❌ FAIL: Camera scanning failed: {e}")
            self.test_results["camera_scanning"] = False
            
    async def test_camera_connection(self):
        """Test camera connection functionality"""
        print("\n🔌 Test 2: Camera Connection")
        print("-" * 30)
        
        try:
            # Get first camera
            cameras = self.camera_vm.get_all_cameras()
            if not cameras:
                print("❌ FAIL: No cameras available for connection test")
                self.test_results["camera_connection"] = False
                return
                
            camera_id = cameras[0].id
            print(f"   Connecting to {camera_id}...")
            
            # Connect camera
            await self.camera_vm.connect(camera_id)
            
            # Wait for completion
            await asyncio.sleep(3)
            
            # Check connection status
            camera_info = self.camera_vm.get_camera_info(camera_id)
            if camera_info and camera_info.status.value == "connected":
                print("✅ PASS: Camera connected successfully")
                self.test_results["camera_connection"] = True
            else:
                print("❌ FAIL: Camera connection failed")
                self.test_results["camera_connection"] = False
                
        except Exception as e:
            print(f"❌ FAIL: Camera connection test failed: {e}")
            self.test_results["camera_connection"] = False
            
    async def test_state_synchronization(self):
        """Test state synchronization between ViewModels"""
        print("\n🔄 Test 3: State Synchronization")
        print("-" * 30)
        
        try:
            # Check if camera is connected in state manager
            connected_cameras = self.state_manager.get_connected_cameras()
            
            if len(connected_cameras) == 1:
                print("✅ PASS: State manager shows 1 connected camera")
                self.test_results["state_synchronization"] = True
            else:
                print(f"❌ FAIL: Expected 1 connected camera, got {len(connected_cameras)}")
                self.test_results["state_synchronization"] = False
                
            # Check if CaptureViewModel can see connected cameras
            capture_cameras = self.capture_vm.get_connected_cameras()
            
            if len(capture_cameras) == 1:
                print("✅ PASS: CaptureViewModel sees connected camera")
            else:
                print(f"❌ FAIL: CaptureViewModel expected 1 camera, got {len(capture_cameras)}")
                self.test_results["state_synchronization"] = False
                
        except Exception as e:
            print(f"❌ FAIL: State synchronization test failed: {e}")
            self.test_results["state_synchronization"] = False
            
    async def test_recording_workflow(self):
        """Test recording workflow"""
        print("\n🎬 Test 4: Recording Workflow")
        print("-" * 30)
        
        try:
            # Get connected camera
            connected_cameras = self.state_manager.get_connected_cameras()
            if not connected_cameras:
                print("❌ FAIL: No connected cameras for recording test")
                self.test_results["recording_workflow"] = False
                return
                
            camera_id = connected_cameras[0].id
            print(f"   Starting recording on {camera_id}...")
            
            # Start recording
            await self.capture_vm.start_recording(camera_id)
            
            # Wait for recording to start
            await asyncio.sleep(2)
            
            # Check if recording started
            if self.capture_vm.is_recording(camera_id):
                print("✅ PASS: Recording started successfully")
                
                # Wait a bit and check recording time
                await asyncio.sleep(3)
                recording_time = self.capture_vm.get_recording_time(camera_id)
                file_size = self.capture_vm.get_file_size(camera_id)
                
                print(f"   📊 Recording time: {recording_time}s")
                print(f"   💾 File size: {file_size}MB")
                
                # Stop recording
                print("   Stopping recording...")
                await self.capture_vm.stop_recording(camera_id)
                await asyncio.sleep(1)
                
                if not self.capture_vm.is_recording(camera_id):
                    print("✅ PASS: Recording stopped successfully")
                    self.test_results["recording_workflow"] = True
                else:
                    print("❌ FAIL: Recording did not stop")
                    self.test_results["recording_workflow"] = False
            else:
                print("❌ FAIL: Recording did not start")
                self.test_results["recording_workflow"] = False
                
        except Exception as e:
            print(f"❌ FAIL: Recording workflow test failed: {e}")
            self.test_results["recording_workflow"] = False
            
    async def test_preview_workflow(self):
        """Test preview workflow"""
        print("\n👁️ Test 5: Preview Workflow")
        print("-" * 30)
        
        try:
            # Get connected camera
            connected_cameras = self.state_manager.get_connected_cameras()
            if not connected_cameras:
                print("❌ FAIL: No connected cameras for preview test")
                self.test_results["preview_workflow"] = False
                return
                
            camera_id = connected_cameras[0].id
            print(f"   Starting preview on {camera_id}...")
            
            # Start preview
            await self.capture_vm.start_preview(camera_id)
            
            # Wait for preview to start
            await asyncio.sleep(1)
            
            # Check if preview started
            if self.capture_vm.is_previewing(camera_id):
                print("✅ PASS: Preview started successfully")
                
                # Wait a bit
                await asyncio.sleep(2)
                
                # Stop preview
                print("   Stopping preview...")
                await self.capture_vm.stop_preview(camera_id)
                await asyncio.sleep(1)
                
                if not self.capture_vm.is_previewing(camera_id):
                    print("✅ PASS: Preview stopped successfully")
                    self.test_results["preview_workflow"] = True
                else:
                    print("❌ FAIL: Preview did not stop")
                    self.test_results["preview_workflow"] = False
            else:
                print("❌ FAIL: Preview did not start")
                self.test_results["preview_workflow"] = False
                
        except Exception as e:
            print(f"❌ FAIL: Preview workflow test failed: {e}")
            self.test_results["preview_workflow"] = False
            
    async def test_error_handling(self):
        """Test error handling"""
        print("\n⚠️ Test 6: Error Handling")
        print("-" * 30)
        
        try:
            # Try to connect to non-existent camera
            print("   Testing connection to non-existent camera...")
            await self.camera_vm.connect("non_existent_camera")
            await asyncio.sleep(1)
            
            # Try to record on non-connected camera
            print("   Testing recording on non-connected camera...")
            await self.capture_vm.start_recording("non_existent_camera")
            await asyncio.sleep(1)
            
            print("✅ PASS: Error handling works (no crashes)")
            self.test_results["error_handling"] = True
            
        except Exception as e:
            print(f"❌ FAIL: Error handling test failed: {e}")
            self.test_results["error_handling"] = False
            
    def print_test_results(self):
        """Print final test results"""
        print("\n" + "=" * 60)
        print("📊 TEST RESULTS SUMMARY")
        print("=" * 60)
        
        total_tests = len(self.test_results)
        passed_tests = sum(1 for result in self.test_results.values() if result)
        failed_tests = total_tests - passed_tests
        
        print(f"Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        
        print("\nDetailed Results:")
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"  {test_name}: {status}")
            
        if failed_tests == 0:
            print("\n🎉 All tests passed! End-to-end workflow is working correctly.")
        else:
            print(f"\n⚠️ {failed_tests} test(s) failed. Please check the implementation.")


async def main():
    """Main test runner"""
    # Create Qt application
    app = QApplication(sys.argv)
    
    # Setup asyncio event loop integration
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    # Run tests
    tester = EndToEndTester()
    await tester.run_all_tests()
    
    # Cleanup
    app.quit()


if __name__ == "__main__":
    # Run the test
    asyncio.run(main())
