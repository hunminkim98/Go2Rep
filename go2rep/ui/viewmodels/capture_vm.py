"""
Capture ViewModel for MVVM pattern

Provides data binding between CaptureAdapter (Model) and CaptureView (View)
using PySide6 Signals for reactive updates.
"""

import asyncio
from PySide6.QtCore import QObject, Signal, QTimer
from typing import Dict, Any, Optional, List
from ...core.di import CameraAdapter
from ...core.state_manager import StateManager


class CaptureViewModel(QObject):
    """
    Capture 상태를 UI에 바인딩하는 ViewModel
    
    Manages recording, preview, and capture settings.
    """
    
    # Signals for UI updates
    recording_started = Signal(str)  # camera_id
    recording_stopped = Signal(str, str)  # camera_id, file_path
    preview_started = Signal(str)  # camera_id
    preview_stopped = Signal(str)  # camera_id
    status_changed = Signal(str, str)  # camera_id, status
    error_occurred = Signal(str)  # error_message
    busy_changed = Signal(bool)  # 작업 중 상태 변경
    recording_time_updated = Signal(str, int)  # camera_id, seconds
    file_size_updated = Signal(str, int)  # camera_id, size_mb
    
    def __init__(self, adapter: CameraAdapter, state_manager: StateManager):
        super().__init__()
        self.adapter = adapter
        self.state_manager = state_manager
        self._recording_cameras: Dict[str, bool] = {}
        self._preview_cameras: Dict[str, bool] = {}
        self._recording_times: Dict[str, int] = {}
        self._file_sizes: Dict[str, int] = {}
        self._is_busy = False
        
        # Recording timer
        self.recording_timer = None
        
        # Connect to state manager signals
        self.state_manager.camera_connected.connect(self.on_camera_connected)
        self.state_manager.camera_disconnected.connect(self.on_camera_disconnected)
        
    def _set_busy(self, busy: bool):
        """작업 중 상태 설정"""
        if self._is_busy != busy:
            self._is_busy = busy
            self.busy_changed.emit(busy)
    
    async def start_recording(self, camera_id: str):
        """녹화 시작"""
        if camera_id in self._recording_cameras:
            return
            
        try:
            self.recording_started.emit(camera_id)
            
            # Mock recording simulation
            await asyncio.sleep(1.0)  # Simulate start delay
            
            self._recording_cameras[camera_id] = True
            self._recording_times[camera_id] = 0
            self._file_sizes[camera_id] = 0
            
            # Start recording timer
            self.start_recording_timer(camera_id)
            
            # Update shared state
            self.state_manager.start_recording(camera_id)
            
            self.status_changed.emit(camera_id, "recording")
            
        except Exception as e:
            self.error_occurred.emit(f"Recording start failed: {str(e)}")
            
    async def stop_recording(self, camera_id: str):
        """녹화 중지"""
        if camera_id not in self._recording_cameras:
            return
            
        try:
            # Get recording time before stopping timer
            recording_time = self._recording_times.get(camera_id, 0)
            
            # Stop recording timer
            self.stop_recording_timer(camera_id)
            
            # Mock file generation
            await asyncio.sleep(0.5)  # Simulate stop delay
            
            file_path = f"/tmp/recording_{camera_id}_{recording_time}.mp4"
            
            # Clean up recording state
            if camera_id in self._recording_cameras:
                del self._recording_cameras[camera_id]
            if camera_id in self._file_sizes:
                del self._file_sizes[camera_id]
            
            # Update shared state
            self.state_manager.stop_recording(camera_id, file_path)
            
            self.recording_stopped.emit(camera_id, file_path)
            self.status_changed.emit(camera_id, "stopped")
            
        except Exception as e:
            self.error_occurred.emit(f"Recording stop failed: {str(e)}")
            
    async def start_preview(self, camera_id: str):
        """프리뷰 시작"""
        if camera_id in self._preview_cameras:
            return
            
        try:
            self.preview_started.emit(camera_id)
            
            # Mock preview simulation
            await asyncio.sleep(0.5)  # Simulate start delay
            
            self._preview_cameras[camera_id] = True
            
            # Update shared state
            self.state_manager.start_preview(camera_id)
            
            self.status_changed.emit(camera_id, "preview")
            
        except Exception as e:
            self.error_occurred.emit(f"Preview start failed: {str(e)}")
            
    async def stop_preview(self, camera_id: str):
        """프리뷰 중지"""
        if camera_id not in self._preview_cameras:
            return
            
        try:
            # Mock preview stop
            await asyncio.sleep(0.2)  # Simulate stop delay
            
            if camera_id in self._preview_cameras:
                del self._preview_cameras[camera_id]
            
            # Update shared state
            self.state_manager.stop_preview(camera_id)
            
            self.preview_stopped.emit(camera_id)
            self.status_changed.emit(camera_id, "idle")
            
        except Exception as e:
            self.error_occurred.emit(f"Preview stop failed: {str(e)}")
            
    def start_recording_timer(self, camera_id: str):
        """녹화 타이머 시작"""
        if self.recording_timer is None:
            self.recording_timer = QTimer()
            self.recording_timer.timeout.connect(self.update_recording_time)
            self.recording_timer.start(1000)  # 1 second interval
            
    def stop_recording_timer(self, camera_id: str):
        """녹화 타이머 중지"""
        if camera_id in self._recording_times:
            del self._recording_times[camera_id]
            
        if not self._recording_times and self.recording_timer:
            self.recording_timer.stop()
            self.recording_timer = None
            
    def update_recording_time(self):
        """녹화 시간 업데이트"""
        for camera_id in list(self._recording_times.keys()):
            self._recording_times[camera_id] += 1
            self.recording_time_updated.emit(camera_id, self._recording_times[camera_id])
            
            # Mock file size increase
            self._file_sizes[camera_id] += 2  # 2MB per second
            self.file_size_updated.emit(camera_id, self._file_sizes[camera_id])
            
    def is_recording(self, camera_id: str) -> bool:
        """녹화 중인지 확인"""
        return self._recording_cameras.get(camera_id, False)
        
    def is_previewing(self, camera_id: str) -> bool:
        """프리뷰 중인지 확인"""
        return self._preview_cameras.get(camera_id, False)
        
    def get_recording_time(self, camera_id: str) -> int:
        """녹화 시간 조회 (초)"""
        return self._recording_times.get(camera_id, 0)
        
    def get_file_size(self, camera_id: str) -> int:
        """파일 크기 조회 (MB)"""
        return self._file_sizes.get(camera_id, 0)
        
    def is_busy(self) -> bool:
        """작업 중인지 확인"""
        return self._is_busy
        
    async def start_recording_many(self, camera_ids: List[str]):
        """여러 카메라 동시 녹화 시작"""
        tasks = [self.start_recording(camera_id) for camera_id in camera_ids]
        await asyncio.gather(*tasks)
        
    async def stop_recording_many(self, camera_ids: List[str]):
        """여러 카메라 동시 녹화 중지"""
        tasks = [self.stop_recording(camera_id) for camera_id in camera_ids]
        await asyncio.gather(*tasks)
        
    def on_camera_connected(self, camera_id: str, camera_info):
        """카메라 연결됨"""
        # Emit signal to update UI
        pass
        
    def on_camera_disconnected(self, camera_id: str):
        """카메라 연결 해제됨"""
        # Stop any ongoing operations
        if camera_id in self._recording_cameras:
            self._recording_cameras[camera_id] = False
        if camera_id in self._preview_cameras:
            self._preview_cameras[camera_id] = False
        if camera_id in self._recording_times:
            del self._recording_times[camera_id]
        if camera_id in self._file_sizes:
            del self._file_sizes[camera_id]
            
    def get_connected_cameras(self):
        """연결된 카메라 목록 조회"""
        return self.state_manager.get_connected_cameras()
