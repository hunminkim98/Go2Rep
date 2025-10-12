"""
Synchronization ViewModel

Manages video synchronization workflows (Manual and Timecode).
"""

import asyncio
from PySide6.QtCore import QObject, Signal, QTimer
from typing import List, Dict, Any, Optional
from ...core.di import CameraAdapter
from ...core.state_manager import StateManager


class SyncViewModel(QObject):
    """
    Synchronization 상태를 UI에 바인딩하는 ViewModel
    
    Manages Manual and Timecode synchronization workflows.
    """

    # Signals for UI updates
    files_changed = Signal(list)  # file_list
    sync_started = Signal(str)  # sync_type (manual/timecode)
    sync_progress = Signal(int)  # progress percentage
    sync_finished = Signal(str, bool)  # sync_type, success
    sync_result = Signal(dict)  # sync results
    error_occurred = Signal(str)  # error_message
    busy_changed = Signal(bool)  # 작업 중 상태 변경
    
    def __init__(self, adapter: CameraAdapter, state_manager: StateManager):
        super().__init__()
        self.adapter = adapter
        self.state_manager = state_manager
        self._files: List[Dict[str, Any]] = []
        self._is_busy = False
        self._sync_task: Optional[asyncio.Task] = None
        
    def _set_busy(self, busy: bool):
        """작업 중 상태 설정"""
        if self._is_busy != busy:
            self._is_busy = busy
            self.busy_changed.emit(busy)
            
    def add_file(self, file_path: str):
        """파일 추가"""
        file_info = {
            "path": file_path,
            "name": file_path.split("/")[-1],
            "size": 0,  # Mock size
            "duration": 0,  # Mock duration
            "offset": 0,  # Manual offset
            "status": "pending"
        }
        
        # Check for duplicates
        if not any(f["path"] == file_path for f in self._files):
            self._files.append(file_info)
            self.files_changed.emit(self._files)
            
    def remove_file(self, file_path: str):
        """파일 제거"""
        self._files = [f for f in self._files if f["path"] != file_path]
        self.files_changed.emit(self._files)
        
    def clear_files(self):
        """모든 파일 제거"""
        self._files.clear()
        self.files_changed.emit(self._files)
        
    def update_offset(self, file_path: str, offset: float):
        """Manual 오프셋 업데이트"""
        for file_info in self._files:
            if file_info["path"] == file_path:
                file_info["offset"] = offset
                break
        self.files_changed.emit(self._files)
        
    async def start_manual_sync(self):
        """Manual 동기화 시작"""
        if self._is_busy or not self._files:
            return
            
        try:
            self._set_busy(True)
            self.sync_started.emit("manual")
            
            # Cancel any existing sync task
            if self._sync_task:
                self._sync_task.cancel()
                
            self._sync_task = asyncio.create_task(self._simulate_manual_sync())
            await self._sync_task
            
        except Exception as e:
            self.error_occurred.emit(f"Manual sync failed: {str(e)}")
        finally:
            self._set_busy(False)
            
    async def _simulate_manual_sync(self):
        """Manual 동기화 시뮬레이션"""
        try:
            # Simulate processing each file
            for i, file_info in enumerate(self._files):
                # Update progress
                progress = int((i / len(self._files)) * 100)
                self.sync_progress.emit(progress)
                
                # Simulate processing time
                await asyncio.sleep(0.5)
                
                # Update file status
                file_info["status"] = "processed"
                self.files_changed.emit(self._files)
                
            # Final progress
            self.sync_progress.emit(100)
            
            # Generate mock results
            results = {
                "sync_type": "manual",
                "total_files": len(self._files),
                "processed_files": len(self._files),
                "total_offset": sum(f["offset"] for f in self._files),
                "output_path": "/tmp/sync_output.json"
            }
            
            self.sync_result.emit(results)
            self.sync_finished.emit("manual", True)
            
        except asyncio.CancelledError:
            self.sync_finished.emit("manual", False)
            raise
            
    async def start_timecode_sync(self):
        """Timecode 동기화 시작"""
        if self._is_busy or not self._files:
            return
            
        try:
            self._set_busy(True)
            self.sync_started.emit("timecode")
            
            # Cancel any existing sync task
            if self._sync_task:
                self._sync_task.cancel()
                
            self._sync_task = asyncio.create_task(self._simulate_timecode_sync())
            await self._sync_task
            
        except Exception as e:
            self.error_occurred.emit(f"Timecode sync failed: {str(e)}")
        finally:
            self._set_busy(False)
            
    async def _simulate_timecode_sync(self):
        """Timecode 동기화 시뮬레이션"""
        try:
            # Simulate FFmpeg timecode analysis
            steps = [
                "Analyzing timecode tracks...",
                "Extracting timecode data...",
                "Calculating offsets...",
                "Generating sync report..."
            ]
            
            for i, step in enumerate(steps):
                # Update progress
                progress = int((i / len(steps)) * 100)
                self.sync_progress.emit(progress)
                
                # Simulate processing time
                await asyncio.sleep(1.0)
                
            # Final progress
            self.sync_progress.emit(100)
            
            # Generate mock results
            results = {
                "sync_type": "timecode",
                "total_files": len(self._files),
                "analyzed_files": len(self._files),
                "detected_offsets": [0.0, 0.5, 1.2],  # Mock offsets
                "output_path": "/tmp/timecode_sync.json"
            }
            
            self.sync_result.emit(results)
            self.sync_finished.emit("timecode", True)
            
        except asyncio.CancelledError:
            self.sync_finished.emit("timecode", False)
            raise
            
    def cancel_sync(self):
        """동기화 취소"""
        if self._sync_task:
            self._sync_task.cancel()
            self._set_busy(False)
            
    def get_files(self) -> List[Dict[str, Any]]:
        """파일 목록 조회"""
        return self._files.copy()
        
    def is_busy(self) -> bool:
        """작업 중인지 확인"""
        return self._is_busy
