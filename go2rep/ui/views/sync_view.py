"""
Video synchronization view

Provides manual and timecode-based synchronization controls
"""

import asyncio
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QFrame, QComboBox, QSpinBox, QCheckBox,
    QGroupBox, QGridLayout, QSlider, QProgressBar,
    QTabWidget, QTextEdit, QFileDialog, QListWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ..widgets.glass_card import GlassCard, NeuroCard
from ..widgets.neuro_button import NeuroButton
from ..widgets.progress_ring import ProgressRing, LoadingSpinner
from ..widgets.file_list import FileListWidget
from ..viewmodels.sync_vm import SyncViewModel


class SyncView(QWidget):
    """동기화 화면"""
    
    # Signals
    sync_started = Signal(str)  # sync_type
    sync_finished = Signal(str, bool)  # sync_type, success
    files_selected = Signal(list)  # file_paths
    
    def __init__(self):
        super().__init__()
        self.viewmodel = None
        self.setup_ui()
        
    def setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header_card = GlassCard()
        
        # Add title
        title_label = QLabel("Video Synchronization")
        title_label.setStyleSheet("""
            QLabel {
                color: rgba(226, 232, 240, 1);
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 8px;
            }
        """)
        header_card.content_layout.addWidget(title_label)
        
        # Sync status
        self.status_label = QLabel("Ready to synchronize")
        self.status_label.setStyleSheet("""
            QLabel {
                color: rgba(34, 197, 94, 1);
                font-size: 16px;
                font-weight: 600;
            }
        """)
        header_card.content_layout.addWidget(self.status_label)
        
        header_card.content_layout.addStretch()
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        header_card.content_layout.addWidget(self.progress_bar)
        
        layout.addWidget(header_card)
        
        # Main content layout
        main_layout = QHBoxLayout()
        
        # Left panel - File management
        file_card = GlassCard("Video Files")
        file_layout = file_card.createVerticalLayout()
        
        # File list widget
        self.file_list_widget = FileListWidget()
        self.file_list_widget.setMaximumHeight(200)
        file_layout.addWidget(self.file_list_widget)
        
        # File management buttons
        file_buttons = QHBoxLayout()
        
        self.add_files_btn = NeuroButton("Add Files", "primary")
        self.remove_file_btn = NeuroButton("Remove", "secondary")
        self.clear_files_btn = NeuroButton("Clear All", "danger")
        
        file_buttons.addWidget(self.add_files_btn)
        file_buttons.addWidget(self.remove_file_btn)
        file_buttons.addWidget(self.clear_files_btn)
        
        file_layout.addLayout(file_buttons)
        
        main_layout.addWidget(file_card)
        
        # Right panel - Sync controls
        controls_card = GlassCard("Synchronization Controls")
        controls_layout = controls_card.createVerticalLayout()
        
        # Tab widget for different sync methods
        self.tab_widget = QTabWidget()
        
        # Manual sync tab
        self.manual_tab = self.create_manual_tab()
        self.tab_widget.addTab(self.manual_tab, "Manual Sync")
        
        # Timecode sync tab
        self.timecode_tab = self.create_timecode_tab()
        self.tab_widget.addTab(self.timecode_tab, "Timecode Sync")
        
        controls_layout.addWidget(self.tab_widget)
        
        # Sync buttons
        sync_buttons = QHBoxLayout()
        
        self.start_sync_btn = NeuroButton("Start Sync", "primary")
        self.cancel_sync_btn = NeuroButton("Cancel", "secondary")
        self.cancel_sync_btn.setEnabled(False)
        
        sync_buttons.addWidget(self.start_sync_btn)
        sync_buttons.addWidget(self.cancel_sync_btn)
        
        controls_layout.addLayout(sync_buttons)
        
        main_layout.addWidget(controls_card)
        
        layout.addLayout(main_layout)
        
        # Results panel
        results_card = GlassCard("Synchronization Results")
        results_layout = results_card.createVerticalLayout()
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(4)
        self.results_table.setHorizontalHeaderLabels(["File", "Offset", "Status", "Notes"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.results_table.setMaximumHeight(150)
        results_layout.addWidget(self.results_table)
        
        # Results text
        self.results_text = QTextEdit()
        self.results_text.setMaximumHeight(100)
        self.results_text.setPlaceholderText("Detailed synchronization results will appear here...")
        results_layout.addWidget(self.results_text)
        
        layout.addWidget(results_card)
        
    def create_manual_tab(self):
        """Manual 동기화 탭 생성"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Manual offset controls
        offset_group = QGroupBox("Manual Offset Settings")
        offset_layout = QGridLayout(offset_group)
        offset_layout.setContentsMargins(16, 16, 16, 16)
        offset_layout.setSpacing(10)
        
        # Offset input
        offset_layout.addWidget(QLabel("Offset (seconds):"), 0, 0)
        self.offset_spinbox = QSpinBox()
        self.offset_spinbox.setRange(-3600, 3600)  # -1 hour to +1 hour
        self.offset_spinbox.setSuffix(" s")
        offset_layout.addWidget(self.offset_spinbox, 0, 1)
        
        # Apply to all checkbox
        self.apply_to_all_cb = QCheckBox("Apply to all files")
        offset_layout.addWidget(self.apply_to_all_cb, 1, 0, 1, 2)
        
        layout.addWidget(offset_group)
        
        # Preview table
        preview_group = QGroupBox("Offset Preview")
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setContentsMargins(16, 16, 16, 16)
        
        self.preview_table = QTableWidget()
        self.preview_table.setColumnCount(3)
        self.preview_table.setHorizontalHeaderLabels(["File", "Original", "With Offset"])
        self.preview_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.preview_table.setMaximumHeight(120)
        preview_layout.addWidget(self.preview_table)
        
        layout.addWidget(preview_group)
        
        return tab
        
    def create_timecode_tab(self):
        """Timecode 동기화 탭 생성"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Timecode settings
        settings_group = QGroupBox("Timecode Settings")
        settings_layout = QGridLayout(settings_group)
        settings_layout.setContentsMargins(16, 16, 16, 16)
        settings_layout.setSpacing(10)
        
        # Reference file selection
        settings_layout.addWidget(QLabel("Reference File:"), 0, 0)
        self.reference_combo = QComboBox()
        settings_layout.addWidget(self.reference_combo, 0, 1)
        
        # Timecode format
        settings_layout.addWidget(QLabel("Timecode Format:"), 1, 0)
        self.format_combo = QComboBox()
        self.format_combo.addItems(["SMPTE", "EBU", "Auto-detect"])
        settings_layout.addWidget(self.format_combo, 1, 1)
        
        layout.addWidget(settings_group)
        
        # Analysis options
        options_group = QGroupBox("Analysis Options")
        options_layout = QVBoxLayout(options_group)
        options_layout.setContentsMargins(16, 16, 16, 16)
        
        self.auto_detect_cb = QCheckBox("Auto-detect timecode tracks")
        self.auto_detect_cb.setChecked(True)
        options_layout.addWidget(self.auto_detect_cb)
        
        self.ignore_drop_cb = QCheckBox("Ignore drop frame")
        options_layout.addWidget(self.ignore_drop_cb)
        
        self.verbose_logging_cb = QCheckBox("Verbose logging")
        options_layout.addWidget(self.verbose_logging_cb)
        
        layout.addWidget(options_group)
        
        return tab
        
    def set_viewmodel(self, viewmodel):
        """ViewModel 설정 및 이벤트 연결"""
        self.viewmodel = viewmodel
        
        # Connect signals
        self.viewmodel.files_changed.connect(self.on_files_changed)
        self.viewmodel.sync_started.connect(self.on_sync_started)
        self.viewmodel.sync_progress.connect(self.on_sync_progress)
        self.viewmodel.sync_finished.connect(self.on_sync_finished)
        self.viewmodel.sync_result.connect(self.on_sync_result)
        self.viewmodel.error_occurred.connect(self.on_error_occurred)
        self.viewmodel.busy_changed.connect(self.on_busy_changed)
        
        # Connect button events
        self.add_files_btn.clicked.connect(self.on_add_files_clicked)
        self.remove_file_btn.clicked.connect(self.on_remove_file_clicked)
        self.clear_files_btn.clicked.connect(self.on_clear_files_clicked)
        self.start_sync_btn.clicked.connect(self.on_start_sync_clicked)
        self.cancel_sync_btn.clicked.connect(self.on_cancel_sync_clicked)
        
        # Connect offset changes
        self.offset_spinbox.valueChanged.connect(self.on_offset_changed)
        
    def on_files_changed(self, files):
        """파일 목록 변경됨"""
        self.file_list_widget.update_files(files)
        self.update_reference_combo(files)
        self.update_preview_table(files)
        
    def update_reference_combo(self, files):
        """Reference 파일 콤보박스 업데이트"""
        self.reference_combo.clear()
        for file_info in files:
            self.reference_combo.addItem(file_info["name"], file_info["path"])
            
    def update_preview_table(self, files):
        """Preview 테이블 업데이트"""
        self.preview_table.setRowCount(len(files))
        
        for i, file_info in enumerate(files):
            # File name
            self.preview_table.setItem(i, 0, QTableWidgetItem(file_info["name"]))
            
            # Original time (mock)
            original_time = "00:00:00"
            self.preview_table.setItem(i, 1, QTableWidgetItem(original_time))
            
            # With offset
            offset = file_info.get("offset", 0)
            offset_time = f"+{offset}s" if offset >= 0 else f"{offset}s"
            self.preview_table.setItem(i, 2, QTableWidgetItem(offset_time))
            
    def on_sync_started(self, sync_type):
        """동기화 시작됨"""
        self.status_label.setText(f"{sync_type.title()} synchronization started...")
        self.status_label.setStyleSheet("""
            QLabel {
                color: rgba(59, 130, 246, 1);
                font-size: 16px;
                font-weight: 600;
            }
        """)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
    def on_sync_progress(self, progress):
        """동기화 진행률 업데이트"""
        self.progress_bar.setValue(progress)
        
    def on_sync_finished(self, sync_type, success):
        """동기화 완료됨"""
        if success:
            self.status_label.setText(f"{sync_type.title()} synchronization completed successfully")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: rgba(34, 197, 94, 1);
                    font-size: 16px;
                    font-weight: 600;
                }
            """)
        else:
            self.status_label.setText(f"{sync_type.title()} synchronization failed")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: rgba(239, 68, 68, 1);
                    font-size: 16px;
                    font-weight: 600;
                }
            """)
            
        self.progress_bar.setVisible(False)
        
    def on_sync_result(self, results):
        """동기화 결과 업데이트"""
        # Update results table
        files = self.viewmodel.get_files()
        self.results_table.setRowCount(len(files))
        
        for i, file_info in enumerate(files):
            self.results_table.setItem(i, 0, QTableWidgetItem(file_info["name"]))
            self.results_table.setItem(i, 1, QTableWidgetItem(f"{file_info.get('offset', 0)}s"))
            self.results_table.setItem(i, 2, QTableWidgetItem(file_info.get("status", "pending")))
            self.results_table.setItem(i, 3, QTableWidgetItem(""))
            
        # Update results text
        result_text = f"""
Synchronization Results:
- Type: {results['sync_type']}
- Total Files: {results['total_files']}
- Processed Files: {results.get('processed_files', results.get('analyzed_files', 0))}
- Output Path: {results['output_path']}
        """.strip()
        
        self.results_text.setText(result_text)
        
    def on_error_occurred(self, error_message):
        """에러 발생"""
        self.status_label.setText(f"Error: {error_message}")
        self.status_label.setStyleSheet("""
            QLabel {
                color: rgba(239, 68, 68, 1);
                font-size: 16px;
                font-weight: 600;
            }
        """)
        self.progress_bar.setVisible(False)
        
    def on_busy_changed(self, busy):
        """작업 중 상태 변경"""
        self.start_sync_btn.setEnabled(not busy)
        self.cancel_sync_btn.setEnabled(busy)
        self.add_files_btn.setEnabled(not busy)
        self.remove_file_btn.setEnabled(not busy)
        self.clear_files_btn.setEnabled(not busy)
        
    def on_add_files_clicked(self):
        """파일 추가 버튼 클릭"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Video Files", "", "Video Files (*.mp4 *.mov *.avi *.mkv)"
        )
        
        for file_path in file_paths:
            self.viewmodel.add_file(file_path)
            
    def on_remove_file_clicked(self):
        """파일 제거 버튼 클릭"""
        selected_files = self.file_list_widget.get_selected_files()
        for file_path in selected_files:
            self.viewmodel.remove_file(file_path)
            
    def on_clear_files_clicked(self):
        """모든 파일 제거 버튼 클릭"""
        self.viewmodel.clear_files()
        
    def on_start_sync_clicked(self):
        """동기화 시작 버튼 클릭"""
        current_tab = self.tab_widget.currentIndex()
        
        if current_tab == 0:  # Manual sync
            asyncio.create_task(self.viewmodel.start_manual_sync())
        elif current_tab == 1:  # Timecode sync
            asyncio.create_task(self.viewmodel.start_timecode_sync())
            
    def on_cancel_sync_clicked(self):
        """동기화 취소 버튼 클릭"""
        self.viewmodel.cancel_sync()
        
    def on_offset_changed(self, value):
        """오프셋 값 변경됨"""
        if self.apply_to_all_cb.isChecked():
            # Apply to all files
            files = self.viewmodel.get_files()
            for file_info in files:
                self.viewmodel.update_offset(file_info["path"], value)
        else:
            # Apply to selected file only
            selected_files = self.file_list_widget.get_selected_files()
            for file_path in selected_files:
                self.viewmodel.update_offset(file_path, value)