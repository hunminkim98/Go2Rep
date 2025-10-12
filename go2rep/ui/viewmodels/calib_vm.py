"""
Calibration ViewModel

Manages camera calibration workflows (intrinsic and extrinsic).
"""

import asyncio
from PySide6.QtCore import QObject, Signal, QTimer
from typing import List, Dict, Any, Optional
from ...core.di import CameraAdapter
from ...core.state_manager import StateManager


class CalibViewModel(QObject):
    """
    Calibration 상태를 UI에 바인딩하는 ViewModel
    
    Manages intrinsic and extrinsic camera calibration workflows.
    """

    # Signals for UI updates
    images_changed = Signal(list)  # image_list
    calibration_started = Signal(str)  # calib_type (intrinsic/extrinsic)
    calibration_progress = Signal(int)  # progress percentage
    calibration_finished = Signal(str, bool)  # calib_type, success
    calibration_result = Signal(dict)  # calibration results
    error_occurred = Signal(str)  # error_message
    busy_changed = Signal(bool)  # 작업 중 상태 변경
    
    def __init__(self, adapter: CameraAdapter, state_manager: StateManager):
        super().__init__()
        self.adapter = adapter
        self.state_manager = state_manager
        self._images: List[Dict[str, Any]] = []
        self._is_busy = False
        self._calibration_task: Optional[asyncio.Task] = None
        
    def _set_busy(self, busy: bool):
        """작업 중 상태 설정"""
        if self._is_busy != busy:
            self._is_busy = busy
            self.busy_changed.emit(busy)
            
    def add_image(self, image_path: str):
        """이미지 추가"""
        image_info = {
            "path": image_path,
            "name": image_path.split("/")[-1],
            "size": 0,  # Mock size
            "status": "pending",
            "corners_detected": False,
            "quality_score": 0.0
        }
        
        # Check for duplicates
        if not any(img["path"] == image_path for img in self._images):
            self._images.append(image_info)
            self.images_changed.emit(self._images)
            
    def remove_image(self, image_path: str):
        """이미지 제거"""
        self._images = [img for img in self._images if img["path"] != image_path]
        self.images_changed.emit(self._images)
        
    def clear_images(self):
        """모든 이미지 제거"""
        self._images.clear()
        self.images_changed.emit(self._images)
        
    async def start_intrinsic_calibration(self):
        """Intrinsic 캘리브레이션 시작"""
        if self._is_busy or not self._images:
            return
            
        try:
            self._set_busy(True)
            self.calibration_started.emit("intrinsic")
            
            # Cancel any existing calibration task
            if self._calibration_task:
                self._calibration_task.cancel()
                
            self._calibration_task = asyncio.create_task(self._simulate_intrinsic_calibration())
            await self._calibration_task
            
        except Exception as e:
            self.error_occurred.emit(f"Intrinsic calibration failed: {str(e)}")
        finally:
            self._set_busy(False)
            
    async def _simulate_intrinsic_calibration(self):
        """Intrinsic 캘리브레이션 시뮬레이션"""
        try:
            # Simulate calibration process
            steps = [
                "Loading calibration images...",
                "Detecting chessboard corners...",
                "Estimating camera parameters...",
                "Optimizing distortion coefficients...",
                "Validating calibration results..."
            ]
            
            for i, step in enumerate(steps):
                # Update progress
                progress = int((i / len(steps)) * 100)
                self.calibration_progress.emit(progress)
                
                # Simulate processing time
                await asyncio.sleep(1.0)
                
                # Update image status
                for img in self._images:
                    if i >= 1:  # After corner detection
                        img["corners_detected"] = True
                        img["quality_score"] = 0.8  # Mock quality score
                        
                self.images_changed.emit(self._images)
                
            # Final progress
            self.calibration_progress.emit(100)
            
            # Generate mock calibration results
            results = {
                "calib_type": "intrinsic",
                "camera_matrix": {
                    "fx": 800.0,
                    "fy": 800.0,
                    "cx": 320.0,
                    "cy": 240.0
                },
                "distortion_coeffs": {
                    "k1": -0.1,
                    "k2": 0.05,
                    "p1": 0.0,
                    "p2": 0.0,
                    "k3": 0.0
                },
                "reprojection_error": 0.5,
                "total_images": len(self._images),
                "valid_images": len(self._images),
                "output_path": "/tmp/intrinsic_calibration.json"
            }
            
            self.calibration_result.emit(results)
            self.calibration_finished.emit("intrinsic", True)
            
        except asyncio.CancelledError:
            self.calibration_finished.emit("intrinsic", False)
            raise
            
    async def start_extrinsic_calibration(self):
        """Extrinsic 캘리브레이션 시작"""
        if self._is_busy:
            return
            
        try:
            self._set_busy(True)
            self.calibration_started.emit("extrinsic")
            
            # Cancel any existing calibration task
            if self._calibration_task:
                self._calibration_task.cancel()
                
            self._calibration_task = asyncio.create_task(self._simulate_extrinsic_calibration())
            await self._calibration_task
            
        except Exception as e:
            self.error_occurred.emit(f"Extrinsic calibration failed: {str(e)}")
        finally:
            self._set_busy(False)
            
    async def _simulate_extrinsic_calibration(self):
        """Extrinsic 캘리브레이션 시뮬레이션"""
        try:
            # Simulate calibration process
            steps = [
                "Loading camera poses...",
                "Estimating relative poses...",
                "Optimizing camera positions...",
                "Validating extrinsic parameters..."
            ]
            
            for i, step in enumerate(steps):
                # Update progress
                progress = int((i / len(steps)) * 100)
                self.calibration_progress.emit(progress)
                
                # Simulate processing time
                await asyncio.sleep(1.2)
                
            # Final progress
            self.calibration_progress.emit(100)
            
            # Generate mock calibration results
            results = {
                "calib_type": "extrinsic",
                "camera_poses": [
                    {"camera_id": "cam_001", "position": [0.0, 0.0, 0.0], "rotation": [0.0, 0.0, 0.0]},
                    {"camera_id": "cam_002", "position": [1.0, 0.0, 0.0], "rotation": [0.0, 0.0, 0.0]},
                    {"camera_id": "cam_003", "position": [0.0, 1.0, 0.0], "rotation": [0.0, 0.0, 0.0]}
                ],
                "reprojection_error": 0.8,
                "total_cameras": 3,
                "output_path": "/tmp/extrinsic_calibration.json"
            }
            
            self.calibration_result.emit(results)
            self.calibration_finished.emit("extrinsic", True)
            
        except asyncio.CancelledError:
            self.calibration_finished.emit("extrinsic", False)
            raise
            
    def cancel_calibration(self):
        """캘리브레이션 취소"""
        if self._calibration_task:
            self._calibration_task.cancel()
            self._set_busy(False)
            
    def get_images(self) -> List[Dict[str, Any]]:
        """이미지 목록 조회"""
        return self._images.copy()
        
    def is_busy(self) -> bool:
        """작업 중인지 확인"""
        return self._is_busy
