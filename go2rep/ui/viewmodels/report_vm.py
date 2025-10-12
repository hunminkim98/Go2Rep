"""
Report ViewModel

Manages report generation workflows (summary and custom reports).
"""

import asyncio
from PySide6.QtCore import QObject, Signal, QTimer
from typing import List, Dict, Any, Optional
from ...core.di import CameraAdapter
from ...core.state_manager import StateManager


class ReportViewModel(QObject):
    """
    Report 상태를 UI에 바인딩하는 ViewModel
    
    Manages summary and custom report generation workflows.
    """

    # Signals for UI updates
    data_sources_changed = Signal(list)  # data_source_list
    report_generation_started = Signal(str)  # report_type (summary/custom)
    report_generation_progress = Signal(int)  # progress percentage
    report_generation_finished = Signal(str, bool)  # report_type, success
    report_generation_result = Signal(dict)  # report results
    error_occurred = Signal(str)  # error_message
    busy_changed = Signal(bool)  # 작업 중 상태 변경
    
    def __init__(self, adapter: CameraAdapter, state_manager: StateManager):
        super().__init__()
        self.adapter = adapter
        self.state_manager = state_manager
        self._data_sources: List[Dict[str, Any]] = []
        self._is_busy = False
        self._report_task: Optional[asyncio.Task] = None
        
    def _set_busy(self, busy: bool):
        """작업 중 상태 설정"""
        if self._is_busy != busy:
            self._is_busy = busy
            self.busy_changed.emit(busy)
            
    def refresh_data_sources(self):
        """데이터 소스 새로고침"""
        # Mock data sources
        mock_sources = [
            {
                "name": "Pose Estimation Results",
                "type": "pose_data",
                "path": "/tmp/pose_estimation.json",
                "size": "2.5 MB",
                "status": "available",
                "selected": True
            },
            {
                "name": "Triangulation Results",
                "type": "triangulation_data",
                "path": "/tmp/triangulation.json",
                "size": "15.8 MB",
                "status": "available",
                "selected": True
            },
            {
                "name": "Tracking Results",
                "type": "tracking_data",
                "path": "/tmp/tracking.json",
                "size": "8.2 MB",
                "status": "available",
                "selected": False
            },
            {
                "name": "Calibration Data",
                "type": "calibration_data",
                "path": "/tmp/intrinsic_calibration.json",
                "size": "0.5 MB",
                "status": "available",
                "selected": True
            }
        ]
        
        self._data_sources = mock_sources
        self.data_sources_changed.emit(self._data_sources)
        
    def toggle_data_source(self, source_name: str):
        """데이터 소스 선택/해제"""
        for source in self._data_sources:
            if source["name"] == source_name:
                source["selected"] = not source["selected"]
                break
        self.data_sources_changed.emit(self._data_sources)
        
    def select_all_data_sources(self):
        """모든 데이터 소스 선택"""
        for source in self._data_sources:
            source["selected"] = True
        self.data_sources_changed.emit(self._data_sources)
        
    def deselect_all_data_sources(self):
        """모든 데이터 소스 해제"""
        for source in self._data_sources:
            source["selected"] = False
        self.data_sources_changed.emit(self._data_sources)
        
    async def start_summary_report(self):
        """요약 리포트 생성 시작"""
        if self._is_busy:
            return
            
        try:
            self._set_busy(True)
            self.report_generation_started.emit("summary")
            
            # Cancel any existing report task
            if self._report_task:
                self._report_task.cancel()
                
            self._report_task = asyncio.create_task(self._simulate_summary_report())
            await self._report_task
            
        except Exception as e:
            self.error_occurred.emit(f"Summary report generation failed: {str(e)}")
        finally:
            self._set_busy(False)
            
    async def _simulate_summary_report(self):
        """요약 리포트 생성 시뮬레이션"""
        try:
            # Simulate report generation process
            steps = [
                "Loading selected data sources...",
                "Analyzing pose estimation results...",
                "Processing triangulation data...",
                "Generating summary statistics...",
                "Creating report document..."
            ]
            
            for i, step in enumerate(steps):
                # Update progress
                progress = int((i / len(steps)) * 100)
                self.report_generation_progress.emit(progress)
                
                # Simulate processing time
                await asyncio.sleep(1.0)
                
            # Final progress
            self.report_generation_progress.emit(100)
            
            # Generate mock results
            selected_sources = [s for s in self._data_sources if s["selected"]]
            results = {
                "report_type": "summary",
                "total_sources": len(self._data_sources),
                "selected_sources": len(selected_sources),
                "report_sections": [
                    "Executive Summary",
                    "Data Quality Assessment",
                    "Key Performance Metrics",
                    "Recommendations"
                ],
                "output_path": "/tmp/summary_report.pdf"
            }
            
            self.report_generation_result.emit(results)
            self.report_generation_finished.emit("summary", True)
            
        except asyncio.CancelledError:
            self.report_generation_finished.emit("summary", False)
            raise
            
    async def start_custom_report(self, sections: List[str]):
        """커스텀 리포트 생성 시작"""
        if self._is_busy:
            return
            
        try:
            self._set_busy(True)
            self.report_generation_started.emit("custom")
            
            # Cancel any existing report task
            if self._report_task:
                self._report_task.cancel()
                
            self._report_task = asyncio.create_task(self._simulate_custom_report(sections))
            await self._report_task
            
        except Exception as e:
            self.error_occurred.emit(f"Custom report generation failed: {str(e)}")
        finally:
            self._set_busy(False)
            
    async def _simulate_custom_report(self, sections: List[str]):
        """커스텀 리포트 생성 시뮬레이션"""
        try:
            # Simulate report generation process
            steps = [
                "Loading selected data sources...",
                "Processing custom sections...",
                "Generating custom content...",
                "Formatting report...",
                "Finalizing document..."
            ]
            
            for i, step in enumerate(steps):
                # Update progress
                progress = int((i / len(steps)) * 100)
                self.report_generation_progress.emit(progress)
                
                # Simulate processing time
                await asyncio.sleep(1.2)
                
            # Final progress
            self.report_generation_progress.emit(100)
            
            # Generate mock results
            selected_sources = [s for s in self._data_sources if s["selected"]]
            results = {
                "report_type": "custom",
                "total_sources": len(self._data_sources),
                "selected_sources": len(selected_sources),
                "custom_sections": sections,
                "output_path": "/tmp/custom_report.pdf"
            }
            
            self.report_generation_result.emit(results)
            self.report_generation_finished.emit("custom", True)
            
        except asyncio.CancelledError:
            self.report_generation_finished.emit("custom", False)
            raise
            
    def cancel_report_generation(self):
        """리포트 생성 취소"""
        if self._report_task:
            self._report_task.cancel()
            self._set_busy(False)
            
    def get_data_sources(self) -> List[Dict[str, Any]]:
        """데이터 소스 목록 조회"""
        return self._data_sources.copy()
        
    def is_busy(self) -> bool:
        """작업 중인지 확인"""
        return self._is_busy
