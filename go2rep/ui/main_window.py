"""
Main application window for PerforMetrics v2.0

Implements the main UI layout with sidebar navigation, top bar,
and stacked content area for different views.
"""

from PySide6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QStackedWidget, QPushButton, QLabel, QFrame
)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QIcon, QFont

from .views.camera_view import CameraView
from .views.capture_view import CaptureView
from .views.sync_view import SyncView
from .views.download_view import DownloadView
from .views.calib_view import CalibView
from .views.analysis_view import AnalysisView
from .views.report_view import ReportView
from .widgets.glass_card import GlassCard
from .widgets.fade_stacked import FadeStackedWidget
from .widgets.scroll_area import SmoothScrollArea
from .widgets.toast import ToastManager


class MainWindow(QMainWindow):
    """
    PerforMetrics v2.0 메인 윈도우
    
    Layout:
    ┌─────────────────────────────────────────┐
    │  Top Bar (Logo, Title, Settings)       │
    ├──────┬──────────────────────────────────┤
    │      │                                  │
    │ Side │  Main Content Area               │
    │ Nav  │  (Stacked Views)                 │
    │      │                                  │
    │      │                                  │
    └──────┴──────────────────────────────────┘
    """
    
    # Signals
    view_changed = Signal(str)  # view_name
    
    def __init__(self, container=None):
        super().__init__()
        self.setWindowTitle("PerforMetrics - Markerless Motion Capture")
        self.setMinimumSize(QSize(1400, 900))
        
        # DI container
        self.container = container
        
        # 상태 관리
        self.current_view = None
        self.views = {}
        self.nav_buttons = {}
        
        # Toast manager
        self.toast_manager = ToastManager(self)
        
        self.setup_ui()
        self.apply_styles()
        
    def setup_ui(self):
        """UI 구성"""
        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        
        # Main layout (horizontal: sidebar + content)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # === Sidebar Navigation ===
        self.sidebar = self.create_sidebar()
        main_layout.addWidget(self.sidebar)
        
        # === Content Area ===
        self.content = QWidget()
        content_layout = QVBoxLayout(self.content)
        content_layout.setContentsMargins(24, 24, 24, 24)
        
        # Top bar
        self.top_bar = self.create_top_bar()
        content_layout.addWidget(self.top_bar)
        
        # Stacked widget for views with fade transitions
        self.stacked_widget = FadeStackedWidget()
        self.stacked_widget.setAnimationDuration(300)
        content_layout.addWidget(self.stacked_widget)
        
        # Create ViewModels
        self.viewmodels = {}
        if self.container:
            from .viewmodels.camera_vm import CameraViewModel
            from .viewmodels.capture_vm import CaptureViewModel
            from .viewmodels.sync_vm import SyncViewModel
            from .viewmodels.download_vm import DownloadViewModel
            from .viewmodels.calib_vm import CalibViewModel
            from .viewmodels.analysis_vm import AnalysisViewModel
            from .viewmodels.report_vm import ReportViewModel
            camera_adapter = self.container.camera_adapter()
            state_manager = self.container.state_manager()
            self.viewmodels["camera"] = CameraViewModel(camera_adapter, state_manager)
            self.viewmodels["capture"] = CaptureViewModel(camera_adapter, state_manager)
            self.viewmodels["sync"] = SyncViewModel(camera_adapter, state_manager)
            download_adapter = self.container.download_adapter()
            self.viewmodels["download"] = DownloadViewModel(download_adapter, state_manager, camera_adapter)
            self.viewmodels["calib"] = CalibViewModel(camera_adapter, state_manager)
            self.viewmodels["analysis"] = AnalysisViewModel(camera_adapter, state_manager)
            self.viewmodels["report"] = ReportViewModel(camera_adapter, state_manager)
        
        # Add views
        self.views = {
            "camera": CameraView(),
            "capture": CaptureView(),
            "sync": SyncView(),
            "download": DownloadView(),
            "calib": CalibView(),
            "analysis": AnalysisView(),
            "report": ReportView()
        }
        
        # Wire ViewModels to Views
        if "camera" in self.viewmodels:
            self.views["camera"].set_viewmodel(self.viewmodels["camera"])
            # Connect error signals to toast
            self.viewmodels["camera"].error_occurred.connect(
                lambda msg: self.toast_manager.show_toast(msg, "error")
            )
        if "capture" in self.viewmodels:
            self.views["capture"].set_viewmodel(self.viewmodels["capture"])
            # Connect error signals to toast
            self.viewmodels["capture"].error_occurred.connect(
                lambda msg: self.toast_manager.show_toast(msg, "error")
            )
        if "sync" in self.viewmodels:
            self.views["sync"].set_viewmodel(self.viewmodels["sync"])
            # Connect error signals to toast
            self.viewmodels["sync"].error_occurred.connect(
                lambda msg: self.toast_manager.show_toast(msg, "error")
            )
        if "download" in self.viewmodels:
            self.views["download"].set_viewmodel(self.viewmodels["download"])
            # Connect error signals to toast
            self.viewmodels["download"].error_occurred.connect(
                lambda msg: self.toast_manager.show_toast(msg, "error")
            )
        if "calib" in self.viewmodels:
            self.views["calib"].set_viewmodel(self.viewmodels["calib"])
            # Connect error signals to toast
            self.viewmodels["calib"].error_occurred.connect(
                lambda msg: self.toast_manager.show_toast(msg, "error")
            )
        if "analysis" in self.viewmodels:
            self.views["analysis"].set_viewmodel(self.viewmodels["analysis"])
            # Connect error signals to toast
            self.viewmodels["analysis"].error_occurred.connect(
                lambda msg: self.toast_manager.show_toast(msg, "error")
            )
        if "report" in self.viewmodels:
            self.views["report"].set_viewmodel(self.viewmodels["report"])
            # Connect error signals to toast
            self.viewmodels["report"].error_occurred.connect(
                lambda msg: self.toast_manager.show_toast(msg, "error")
            )
        
        # Create scroll areas for each view
        self.scroll_areas = {}
        for key, view in self.views.items():
            sa = SmoothScrollArea()
            sa.setObjectName(f"Scroll_{key}")
            sa.setWidget(view)
            self.scroll_areas[key] = sa
            self.stacked_widget.addWidget(sa)
            
        main_layout.addWidget(self.content, stretch=1)
        
        # Add toast manager to main layout
        main_layout.addWidget(self.toast_manager)
        
        # Show camera view by default
        self.show_view("camera")
        
    def create_sidebar(self):
        """Glassmorphism 스타일 사이드바"""
        sidebar = QFrame()
        sidebar.setObjectName("Sidebar")
        sidebar.setFixedWidth(240)
        
        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 24, 16, 24)
        layout.setSpacing(8)
        
        # Logo
        logo = QLabel("PerforMetrics")
        logo.setStyleSheet("""
            QLabel {
                color: rgba(226, 232, 240, 1);
                font-size: 24px;
                font-weight: bold;
                margin-bottom: 32px;
            }
        """)
        layout.addWidget(logo)
        
        # Navigation buttons
        nav_items = [
            ("camera", "Cameras", "camera"),
            ("capture", "Capture", "capture"),
            ("download", "Downloads", "download"),
            ("sync", "Synchronize", "sync"),
            ("calib", "Calibrate", "calib"),
            ("analysis", "Analyze", "analysis"),
            ("report", "Report", "report"),
        ]
        
        self.nav_buttons = {}
        for key, label, icon in nav_items:
            btn = QPushButton(label)
            btn.setObjectName("NavButton")
            btn.setCheckable(True)
            btn.clicked.connect(lambda checked, k=key: self.show_view(k))
            layout.addWidget(btn)
            self.nav_buttons[key] = btn
            
        layout.addStretch()
        
        # Settings button at bottom
        settings_btn = QPushButton("Settings")
        settings_btn.setObjectName("NavButton")
        settings_btn.clicked.connect(self.on_settings_clicked)
        layout.addWidget(settings_btn)
        
        return sidebar
        
    def create_top_bar(self):
        """상단 바 (breadcrumb, quick actions)"""
        top_bar = GlassCard()
        layout = top_bar.createHorizontalLayout()
        
        # Breadcrumb
        self.breadcrumb = QLabel("Home > Cameras")
        self.breadcrumb.setStyleSheet("""
            QLabel {
                color: rgba(148, 163, 184, 1);
                font-size: 14px;
            }
        """)
        layout.addWidget(self.breadcrumb)
        
        layout.addStretch()
        
        # Quick actions
        help_btn = QPushButton("❓ Help")
        help_btn.setProperty("class", "secondary")
        help_btn.clicked.connect(self.on_help_clicked)
        layout.addWidget(help_btn)
        
        return top_bar
        
    def show_view(self, view_name):
        """뷰 전환 + breadcrumb 업데이트"""
        if view_name in self.scroll_areas:
            self.stacked_widget.setCurrentWidget(self.scroll_areas[view_name])
            self.current_view = view_name
            
            # Update breadcrumb
            view_titles = {
                "camera": "Cameras",
                "capture": "Capture",
                "sync": "Synchronization",
                "download": "Downloads",
                "calib": "Calibration",
                "analysis": "3D Analysis",
                "report": "Report"
            }
            self.breadcrumb.setText(f"Home > {view_titles.get(view_name, '')}")
            
            # Update nav buttons
            for key, btn in self.nav_buttons.items():
                btn.setChecked(key == view_name)
                
            # Emit signal
            self.view_changed.emit(view_name)
                
    def apply_styles(self):
        """QSS 스타일시트 로드"""
        try:
            with open("go2rep/ui/styles/glass.qss", "r") as f:
                self.setStyleSheet(f.read())
        except FileNotFoundError:
            # Fallback to basic styling if QSS file not found
            self.setStyleSheet("""
                QMainWindow {
                    background-color: rgba(15, 23, 42, 1);
                    color: rgba(226, 232, 240, 1);
                }
                QWidget {
                    background-color: transparent;
                    color: rgba(226, 232, 240, 1);
                }
            """)
            
    def on_settings_clicked(self):
        """설정 버튼 클릭"""
        # TODO: Implement settings dialog
        print("Settings clicked")
        
    def on_help_clicked(self):
        """도움말 버튼 클릭"""
        # TODO: Implement help dialog
        print("Help clicked")
        
    def get_current_view(self):
        """현재 뷰 반환"""
        return self.current_view
        
    def get_view(self, view_name):
        """특정 뷰 반환"""
        return self.views.get(view_name)
        
    def set_viewmodel(self, view_name, viewmodel):
        """특정 뷰에 ViewModel 주입"""
        if view_name in self.views:
            view = self.views[view_name]
            if hasattr(view, 'set_viewmodel'):
                view.set_viewmodel(viewmodel)
                
    def closeEvent(self, event):
        """윈도우 종료 이벤트"""
        # TODO: Save settings, cleanup resources
        event.accept()