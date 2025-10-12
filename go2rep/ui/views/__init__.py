"""
Views for Go2Rep v2.0

Contains all view components for different workflows
"""

from .camera_view import CameraView
from .capture_view import CaptureView
from .sync_view import SyncView
from .download_view import DownloadView
from .calib_view import CalibView
from .analysis_view import AnalysisView
from .report_view import ReportView

__all__ = [
    'CameraView',
    'CaptureView',
    'SyncView',
    'DownloadView',
    'CalibView',
    'AnalysisView',
    'ReportView'
]
