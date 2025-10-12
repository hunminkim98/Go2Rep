"""
Camera ViewModel for MVVM pattern

Provides data binding between CameraAdapter (Model) and CameraView (View)
using PySide6 Signals for reactive updates.
"""

import asyncio
from PySide6.QtCore import QObject, Signal
from typing import List, Dict, Any, Optional
from ...core.di import CameraAdapter
from ...core.models import CameraInfo, CameraStatus
from ...core.state_manager import StateManager


class CameraViewModel(QObject):
    """
    Camera 상태를 UI에 바인딩하는 ViewModel
    
    Uses CameraAdapter through dependency injection for camera operations.
    """
    
    # Signals for UI updates
    cameras_changed = Signal(list)  # Camera 리스트 변경 시 emit
    status_changed = Signal(str, str)  # camera_id, new_status
    scan_started = Signal()  # 스캔 시작
    scan_finished = Signal(list)  # 스캔 완료, 결과 리스트
    connection_started = Signal(str)  # 연결 시작, camera_id
    connection_finished = Signal(str, bool)  # 연결 완료, camera_id, success
    error_occurred = Signal(str)  # 에러 발생, error_message
    busy_changed = Signal(bool)  # 작업 중 상태 변경
    
    def __init__(self, adapter: CameraAdapter, state_manager: StateManager):
        super().__init__()
        self.adapter = adapter
        self.state_manager = state_manager
        self._cameras: Dict[str, CameraInfo] = {}
        self._is_busy = False
    
    def _set_busy(self, busy: bool):
        """작업 중 상태 설정"""
        if self._is_busy != busy:
            self._is_busy = busy
            self.busy_changed.emit(busy)
    
    async def scan(self):
        """카메라 스캔"""
        if self._is_busy:
            return
            
        try:
            self._set_busy(True)
            self.scan_started.emit()
            
            cameras = await self.adapter.scan()
            
            # Update internal state
            self._cameras.clear()
            for camera in cameras:
                self._cameras[camera.id] = camera
                
            self.scan_finished.emit(cameras)
            self.cameras_changed.emit(cameras)
            
        except Exception as e:
            self.error_occurred.emit(f"Scan failed: {str(e)}")
        finally:
            self._set_busy(False)
            
    async def connect(self, camera_id: str):
        """카메라 연결"""
        if self._is_busy or camera_id not in self._cameras:
            return
            
        try:
            self._set_busy(True)
            self.connection_started.emit(camera_id)
            
            success = await self.adapter.connect(camera_id)
            
            if success:
                # Update camera status
                self._cameras[camera_id].status = CameraStatus.CONNECTED
                self.status_changed.emit(camera_id, CameraStatus.CONNECTED.value)
                
                # Update shared state
                self.state_manager.connect_camera(camera_id, self._cameras[camera_id])
                
            self.connection_finished.emit(camera_id, success)
            
        except Exception as e:
            self.error_occurred.emit(f"Connection failed: {str(e)}")
        finally:
            self._set_busy(False)
            
    async def disconnect(self, camera_id: str):
        """카메라 연결 해제"""
        if self._is_busy or camera_id not in self._cameras:
            return
            
        try:
            self._set_busy(True)
            
            success = await self.adapter.disconnect(camera_id)
            
            if success:
                # Update camera status
                self._cameras[camera_id].status = CameraStatus.DISCONNECTED
                self.status_changed.emit(camera_id, CameraStatus.DISCONNECTED.value)
                
                # Update shared state
                self.state_manager.disconnect_camera(camera_id)
                
            self.connection_finished.emit(camera_id, success)
            
        except Exception as e:
            self.error_occurred.emit(f"Disconnection failed: {str(e)}")
        finally:
            self._set_busy(False)
            
    def get_camera_info(self, camera_id: str) -> Optional[CameraInfo]:
        """카메라 정보 조회"""
        return self._cameras.get(camera_id)
        
    def get_all_cameras(self) -> List[CameraInfo]:
        """모든 카메라 정보 조회"""
        return list(self._cameras.values())
        
    def is_busy(self) -> bool:
        """작업 중인지 확인"""
        return self._is_busy
        
    def get_camera_status(self, camera_id: str) -> Optional[CameraStatus]:
        """카메라 상태 조회"""
        camera = self._cameras.get(camera_id)
        return camera.status if camera else None
        
    async def connect_all(self, cameras: List[CameraInfo]):
        """모든 카메라에 연결"""
        if self._is_busy or not cameras:
            return
            
        try:
            self._set_busy(True)
            
            # 모든 카메라에 동시에 연결 시도
            tasks = [self.adapter.connect(camera.id) for camera in cameras]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 결과 처리
            for camera, result in zip(cameras, results):
                if isinstance(result, Exception):
                    self.error_occurred.emit(f"Failed to connect {camera.id}: {str(result)}")
                elif result:
                    # 연결 성공
                    self._cameras[camera.id].status = CameraStatus.CONNECTED
                    self.status_changed.emit(camera.id, CameraStatus.CONNECTED.value)
                    self.state_manager.connect_camera(camera.id, self._cameras[camera.id])
                    self.connection_finished.emit(camera.id, True)
                else:
                    # 연결 실패
                    self.connection_finished.emit(camera.id, False)
                    
        except Exception as e:
            self.error_occurred.emit(f"Bulk connection failed: {str(e)}")
        finally:
            self._set_busy(False)
            
    async def disconnect_all(self, cameras: List[CameraInfo]):
        """모든 카메라에서 연결 해제"""
        if self._is_busy or not cameras:
            return
            
        try:
            self._set_busy(True)
            
            # 모든 카메라에서 동시에 연결 해제 시도
            tasks = [self.adapter.disconnect(camera.id) for camera in cameras]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 결과 처리
            for camera, result in zip(cameras, results):
                if isinstance(result, Exception):
                    self.error_occurred.emit(f"Failed to disconnect {camera.id}: {str(result)}")
                elif result:
                    # 연결 해제 성공
                    self._cameras[camera.id].status = CameraStatus.DISCONNECTED
                    self.status_changed.emit(camera.id, CameraStatus.DISCONNECTED.value)
                    self.state_manager.disconnect_camera(camera.id)
                    self.connection_finished.emit(camera.id, True)
                else:
                    # 연결 해제 실패
                    self.connection_finished.emit(camera.id, False)
                    
        except Exception as e:
            self.error_occurred.emit(f"Bulk disconnection failed: {str(e)}")
        finally:
            self._set_busy(False)
