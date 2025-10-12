"""
Download ViewModel

Manages GoPro video download workflows.
"""

import asyncio
from PySide6.QtCore import QObject, Signal, QTimer
from typing import List, Dict, Any, Optional, Set
from pathlib import Path
from ...core.download import DownloadAdapter, get_download_path
from ...core.state_manager import StateManager


class DownloadViewModel(QObject):
    """
    Download 상태를 UI에 바인딩하는 ViewModel
    
    Manages video download from connected GoPros to local machine.
    """

    # Signals for UI updates
    files_changed = Signal(str, list)  # camera_id, files_list
    download_started = Signal(str, str)  # camera_id, filename
    download_progress = Signal(str, str, int)  # camera_id, filename, progress
    download_finished = Signal(str, str, str)  # camera_id, filename, result_path
    download_failed = Signal(str, str, str)  # camera_id, filename, error
    error_occurred = Signal(str)  # error_message
    busy_changed = Signal(bool)  # 작업 중 상태 변경
    cameras_scanned = Signal(list)  # cameras_list
    camera_connected = Signal(str, object)  # camera_id, camera_info
    
    def __init__(self, adapter: DownloadAdapter, state_manager: StateManager, camera_adapter=None):
        super().__init__()
        self.adapter = adapter
        self.state_manager = state_manager
        self.camera_adapter = camera_adapter
        self._files: Dict[str, List[Dict]] = {}  # camera_id -> files
        self._downloads: Dict[str, Dict[str, asyncio.Task]] = {}  # camera_id -> {filename -> task}
        self._is_busy = False
        self._semaphore = asyncio.Semaphore(3)  # Limit concurrent downloads
        
        # Connect to state manager
        self.state_manager.camera_connected.connect(self.on_camera_connected)
        self.state_manager.camera_disconnected.connect(self.on_camera_disconnected)
        
    def _set_busy(self, busy: bool):
        """작업 중 상태 설정"""
        if self._is_busy != busy:
            self._is_busy = busy
            self.busy_changed.emit(busy)
    
    def on_camera_connected(self, camera_id: str, camera_info):
        """카메라 연결됨"""
        # Initialize files list for new camera
        if camera_id not in self._files:
            self._files[camera_id] = []
            
    def on_camera_disconnected(self, camera_id: str):
        """카메라 연결 해제됨"""
        # Cancel any ongoing downloads
        self.cancel_downloads(camera_id)
        
        # Clear files list
        if camera_id in self._files:
            del self._files[camera_id]
            self.files_changed.emit(camera_id, [])
    
    async def scan_files(self, camera_id: str):
        """카메라에서 파일 목록 스캔"""
        if self._is_busy:
            return
            
        try:
            self._set_busy(True)
            
            # Get files from adapter
            files = await self.adapter.list_files(camera_id)
            
            # Store files
            self._files[camera_id] = files
            
            # Emit signal
            self.files_changed.emit(camera_id, files)
            
        except Exception as e:
            self.error_occurred.emit(f"Scan failed for {camera_id}: {str(e)}")
        finally:
            self._set_busy(False)
    
    async def download_file(self, camera_id: str, file: Dict):
        """단일 파일 다운로드"""
        if camera_id not in self._files:
            self.error_occurred.emit(f"Camera {camera_id} not found")
            return
            
        filename = file["name"]
        
        # Check if already downloading
        if camera_id in self._downloads and filename in self._downloads[camera_id]:
            return
            
        try:
            # Get download path
            dest_dir = get_download_path(camera_id)
            
            # Create progress callback
            def progress_callback(progress: int):
                self.download_progress.emit(camera_id, filename, progress)
            
            # Start download task
            async def download_task():
                async with self._semaphore:
                    try:
                        self.download_started.emit(camera_id, filename)
                        
                        result_path = await self.adapter.download(
                            camera_id, file, dest_dir, progress_callback
                        )
                        
                        self.download_finished.emit(camera_id, filename, str(result_path))
                        
                    except asyncio.CancelledError:
                        self.download_failed.emit(camera_id, filename, "Cancelled")
                        raise
                    except Exception as e:
                        self.download_failed.emit(camera_id, filename, str(e))
                    finally:
                        # Clean up task reference
                        if camera_id in self._downloads and filename in self._downloads[camera_id]:
                            del self._downloads[camera_id][filename]
                            if not self._downloads[camera_id]:
                                del self._downloads[camera_id]
            
            # Store task reference
            if camera_id not in self._downloads:
                self._downloads[camera_id] = {}
            
            task = asyncio.create_task(download_task())
            self._downloads[camera_id][filename] = task
            
        except Exception as e:
            self.error_occurred.emit(f"Download failed for {filename}: {str(e)}")
    
    async def download_selected(self, camera_id: str, selected_files: List[Dict]):
        """선택된 파일들 다운로드"""
        if not selected_files:
            return
            
        # Create download tasks
        tasks = []
        for file in selected_files:
            task = asyncio.create_task(self.download_file(camera_id, file))
            tasks.append(task)
        
        # Wait for all downloads to complete
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            self.error_occurred.emit(f"Bulk download failed: {str(e)}")
    
    async def download_all(self, camera_id: str):
        """모든 파일 다운로드"""
        if camera_id not in self._files:
            self.error_occurred.emit(f"Camera {camera_id} not found")
            return
            
        files = self._files[camera_id]
        if not files:
            self.error_occurred.emit(f"No files found for camera {camera_id}")
            return
            
        await self.download_selected(camera_id, files)
    
    async def download_all_cameras(self):
        """모든 연결된 카메라의 파일 다운로드"""
        connected_cameras = self.state_manager.get_connected_cameras()
        
        if not connected_cameras:
            self.error_occurred.emit("No connected cameras found")
            return
            
        # Create download tasks for all cameras
        tasks = []
        for camera_id in connected_cameras:
            if camera_id in self._files and self._files[camera_id]:
                task = asyncio.create_task(self.download_all(camera_id))
                tasks.append(task)
        
        if not tasks:
            self.error_occurred.emit("No files found on any camera")
            return
            
        # Wait for all downloads to complete
        try:
            await asyncio.gather(*tasks, return_exceptions=True)
        except Exception as e:
            self.error_occurred.emit(f"Multi-camera download failed: {str(e)}")
    
    def cancel_downloads(self, camera_id: str):
        """카메라의 다운로드 취소"""
        if camera_id in self._downloads:
            for filename, task in self._downloads[camera_id].items():
                if not task.done():
                    task.cancel()
            
            # Clear task references
            del self._downloads[camera_id]
            
            # Cancel in adapter
            self.adapter.cancel(camera_id)
    
    def cancel_all_downloads(self):
        """모든 다운로드 취소"""
        for camera_id in list(self._downloads.keys()):
            self.cancel_downloads(camera_id)
    
    def get_files(self, camera_id: str) -> List[Dict]:
        """카메라의 파일 목록 조회"""
        return self._files.get(camera_id, [])
    
    def get_connected_cameras(self) -> List[str]:
        """연결된 카메라 목록 조회"""
        return self.state_manager.get_connected_camera_ids()
    
    def is_downloading(self, camera_id: str, filename: str) -> bool:
        """파일이 다운로드 중인지 확인"""
        return (camera_id in self._downloads and 
                filename in self._downloads[camera_id] and
                not self._downloads[camera_id][filename].done())
    
    def is_busy(self) -> bool:
        """작업 중인지 확인"""
        return self._is_busy
    
    def get_download_path(self, camera_id: str) -> Path:
        """다운로드 경로 조회"""
        return get_download_path(camera_id)
    
    async def scan_cameras(self):
        """카메라 스캔"""
        if not self.camera_adapter:
            self.error_occurred.emit("Camera adapter not available")
            return
            
        try:
            self._set_busy(True)
            cameras = await self.camera_adapter.scan()
            self.cameras_scanned.emit(cameras)
        except Exception as e:
            self.error_occurred.emit(f"Camera scan failed: {str(e)}")
        finally:
            self._set_busy(False)
    
    async def connect_camera(self, camera_id: str):
        """카메라 연결"""
        if not self.camera_adapter:
            self.error_occurred.emit("Camera adapter not available")
            return
            
        try:
            self._set_busy(True)
            success = await self.camera_adapter.connect(camera_id)
            
            if success:
                # Get camera info and update state manager
                camera_info = await self.camera_adapter.get_status(camera_id)
                # Note: This would need to be implemented properly
                # For now, we'll emit a signal for the UI to handle
                self.camera_connected.emit(camera_id, camera_info)
            else:
                self.error_occurred.emit(f"Failed to connect to camera {camera_id}")
                
        except Exception as e:
            self.error_occurred.emit(f"Camera connection failed: {str(e)}")
        finally:
            self._set_busy(False)
