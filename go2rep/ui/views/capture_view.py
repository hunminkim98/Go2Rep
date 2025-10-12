"""
Camera capture control view

Provides controls for starting/stopping recording, settings, and live preview
"""

import asyncio
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QFrame, QComboBox, QSpinBox, QCheckBox,
    QGroupBox, QGridLayout, QSlider, QListWidget, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont, QColor

from ..widgets.glass_card import GlassCard, NeuroCard
from ..widgets.neuro_button import NeuroButton
from ..widgets.progress_ring import ProgressRing
from ..viewmodels.capture_vm import CaptureViewModel


class CaptureView(QWidget):
    """카메라 촬영 제어 화면"""
    
    # Signals
    start_recording = Signal(list)  # camera_ids
    stop_recording = Signal(list)  # camera_ids
    settings_changed = Signal(dict)  # settings
    
    def __init__(self):
        super().__init__()
        self.viewmodel = None
        self.connected_cameras = []
        self.setup_ui()
        
    def setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header_card = GlassCard()
        
        # Add title
        title_label = QLabel("Capture Control")
        title_label.setStyleSheet("""
            QLabel {
                color: rgba(226, 232, 240, 1);
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 8px;
            }
        """)
        header_card.content_layout.addWidget(title_label)
        
        # Recording status
        self.status_label = QLabel("Ready to record")
        self.status_label.setStyleSheet("""
            QLabel {
                color: rgba(34, 197, 94, 1);
                font-size: 16px;
                font-weight: 600;
            }
        """)
        header_card.content_layout.addWidget(self.status_label)
        
        header_card.content_layout.addStretch()
        
        # Recording time
        self.time_label = QLabel("00:00:00")
        self.time_label.setStyleSheet("""
            QLabel {
                color: rgba(226, 232, 240, 1);
                font-size: 18px;
                font-weight: bold;
                font-family: "Courier New", monospace;
            }
        """)
        header_card.content_layout.addWidget(self.time_label)
        
        layout.addWidget(header_card)
        
        # Camera list
        camera_card = GlassCard("Connected Cameras")
        self.camera_list = QListWidget()
        self.camera_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.camera_list.setStyleSheet("""
            QListWidget {
                background-color: rgba(21, 21, 21, 0.9);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 8px;
                color: rgba(226, 232, 240, 1);
                font-size: 13px;
            }
            QListWidget::item {
                padding: 8px;
                border-radius: 4px;
                margin: 2px;
            }
            QListWidget::item:selected {
                background-color: rgba(226, 232, 240, 0.15);
            }
            QListWidget::item:hover {
                background-color: rgba(255, 255, 255, 0.05);
            }
        """)
        camera_card.content_layout.addWidget(self.camera_list)
        layout.addWidget(camera_card)
        
        # Main content layout
        main_layout = QHBoxLayout()
        
        # Left panel - Controls
        controls_card = GlassCard("Recording Controls")
        controls_layout = controls_card.createVerticalLayout()
        
        # Camera selection
        camera_group = QGroupBox("Cameras")
        camera_layout = QVBoxLayout(camera_group)
        
        # Camera list is already defined above, no need to redefine
        camera_layout.addWidget(QLabel("Connected cameras are shown above"))
        
        controls_layout.addWidget(camera_group)
        
        # Recording controls
        record_group = QGroupBox("Recording")
        record_layout = QVBoxLayout(record_group)
        
        # Start/Stop buttons
        button_layout = QHBoxLayout()
        
        self.start_btn = NeuroButton("Start Recording", "danger")
        # self.start_btn.clicked.connect(self.on_start_recording)  # Will be connected in set_viewmodel
        button_layout.addWidget(self.start_btn)
        
        self.stop_btn = NeuroButton("Stop Recording", "secondary")
        # self.stop_btn.clicked.connect(self.on_stop_recording)  # Will be connected in set_viewmodel
        self.stop_btn.setEnabled(False)
        button_layout.addWidget(self.stop_btn)
        
        record_layout.addLayout(button_layout)
        
        # All cameras buttons
        all_button_layout = QHBoxLayout()
        
        self.start_all_btn = NeuroButton("Start Recording All", "success")
        all_button_layout.addWidget(self.start_all_btn)
        
        self.stop_all_btn = NeuroButton("Stop Recording All", "secondary")
        self.stop_all_btn.setEnabled(False)
        all_button_layout.addWidget(self.stop_all_btn)
        
        record_layout.addLayout(all_button_layout)
        controls_layout.addWidget(record_group)
        
        # Settings
        settings_group = QGroupBox("Settings")
        settings_layout = QGridLayout(settings_group)
        
        # Resolution
        settings_layout.addWidget(QLabel("Resolution:"), 0, 0)
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(["4K", "2.7K", "1080p", "720p"])
        self.resolution_combo.setCurrentText("1080p")
        settings_layout.addWidget(self.resolution_combo, 0, 1)
        
        # Frame rate
        settings_layout.addWidget(QLabel("Frame Rate:"), 1, 0)
        self.fps_combo = QComboBox()
        self.fps_combo.addItems(["60fps", "30fps", "24fps"])
        self.fps_combo.setCurrentText("30fps")
        settings_layout.addWidget(self.fps_combo, 1, 1)
        
        # Field of view
        settings_layout.addWidget(QLabel("Field of View:"), 2, 0)
        self.fov_combo = QComboBox()
        self.fov_combo.addItems(["Wide", "Linear", "Narrow"])
        self.fov_combo.setCurrentText("Wide")
        settings_layout.addWidget(self.fov_combo, 2, 1)
        
        # Stabilization
        self.stabilization_check = QCheckBox("Enable Stabilization")
        self.stabilization_check.setChecked(True)
        settings_layout.addWidget(self.stabilization_check, 3, 0, 1, 2)
        
        controls_layout.addWidget(settings_group)
        
        main_layout.addWidget(controls_card)
        
        # Right panel - Preview
        preview_card = GlassCard("Live Preview")
        preview_layout = preview_card.createVerticalLayout()
        
        # Preview placeholder
        self.preview_label = QLabel("No preview available")
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: rgba(30, 41, 59, 0.6);
                border: 2px dashed rgba(71, 85, 105, 0.5);
                border-radius: 8px;
                color: rgba(148, 163, 184, 1);
                font-size: 16px;
                font-style: italic;
                min-height: 300px;
            }
        """)
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(self.preview_label)
        
        # Preview controls
        preview_controls = QHBoxLayout()
        
        self.preview_btn = NeuroButton("Start Preview", "primary")
        # self.preview_btn.clicked.connect(self.on_start_preview)  # Will be connected in set_viewmodel
        preview_controls.addWidget(self.preview_btn)
        
        self.preview_stop_btn = NeuroButton("Stop Preview", "secondary")
        # self.preview_stop_btn.clicked.connect(self.on_stop_preview)  # Will be connected in set_viewmodel
        self.preview_stop_btn.setEnabled(False)
        preview_controls.addWidget(self.preview_stop_btn)
        
        preview_controls.addStretch()
        
        # Battery indicator
        self.battery_label = QLabel("Battery: N/A")
        self.battery_label.setStyleSheet("""
            QLabel {
                color: rgba(148, 163, 184, 1);
                font-size: 12px;
            }
        """)
        preview_controls.addWidget(self.battery_label)
        
        preview_layout.addLayout(preview_controls)
        
        main_layout.addWidget(preview_card)
        
        layout.addLayout(main_layout)
        
        # Bottom panel - Status
        status_card = GlassCard("Recording Status")
        status_layout = status_card.createVerticalLayout()
        
        # Status table
        self.status_table = QTableWidget()
        self.status_table.setColumnCount(5)
        self.status_table.setHorizontalHeaderLabels(["Camera", "Status", "Time", "Size (MB)", "Last File"])
        self.status_table.horizontalHeader().setStretchLastSection(True)
        self.status_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.status_table.verticalHeader().setVisible(False)
        self.status_table.setAlternatingRowColors(True)
        self.status_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.status_table.setMinimumHeight(300)
        self.status_table.setMaximumHeight(500)
        self.status_table.verticalHeader().setDefaultSectionSize(35)
        self.status_table.setStyleSheet("""
            QTableWidget {
                background-color: rgba(21, 21, 21, 0.9);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                color: rgba(226, 232, 240, 1);
                font-size: 12px;
                gridline-color: rgba(255, 255, 255, 0.1);
            }
            QTableWidget::item {
                padding: 4px;
                border: none;
            }
            QTableWidget::item:selected {
                background-color: rgba(226, 232, 240, 0.15);
            }
            QHeaderView::section {
                background-color: rgba(30, 30, 30, 0.9);
                color: rgba(226, 232, 240, 1);
                padding: 8px;
                border: none;
                font-weight: 600;
            }
        """)
        
        # Maintain row mapping
        self.row_by_camera = {}
        
        status_layout.addWidget(self.status_table)
        
        layout.addWidget(status_card)
        
    def set_viewmodel(self, vm):
        """ViewModel 주입"""
        self.viewmodel = vm
        # TODO: Connect signals when ViewModel is implemented
        
    def on_start_recording(self):
        """녹화 시작"""
        self.start_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.status_label.setText("Recording...")
        self.status_label.setStyleSheet("""
            QLabel {
                color: rgba(239, 68, 68, 1);
                font-size: 16px;
                font-weight: 600;
            }
        """)
        self.recording_status.setText("Recording in progress")
        
        # Emit signal
        self.start_recording.emit([])  # TODO: Get selected camera IDs
        
    def on_stop_recording(self):
        """녹화 정지"""
        if not self.viewmodel:
            return
            
        # Get currently recording cameras
        recording_cameras = []
        for camera_id in self.connected_cameras:
            if self.viewmodel.is_recording(camera_id):
                recording_cameras.append(camera_id)
        
        if not recording_cameras:
            self.on_error_occurred("No cameras are currently recording")
            return
            
        # Stop recording on all recording cameras
        for camera_id in recording_cameras:
            asyncio.create_task(self.viewmodel.stop_recording(camera_id))
        
    def set_viewmodel(self, viewmodel):
        """ViewModel 설정 및 이벤트 연결"""
        self.viewmodel = viewmodel
        
        # Connect signals
        self.viewmodel.recording_started.connect(self.on_recording_started)
        self.viewmodel.recording_stopped.connect(self.on_recording_stopped)
        self.viewmodel.preview_started.connect(self.on_preview_started)
        self.viewmodel.preview_stopped.connect(self.on_preview_stopped)
        self.viewmodel.status_changed.connect(self.on_status_changed)
        self.viewmodel.error_occurred.connect(self.on_error_occurred)
        self.viewmodel.recording_time_updated.connect(self.on_recording_time_updated)
        self.viewmodel.file_size_updated.connect(self.on_file_size_updated)
        
        # Connect button events
        self.start_btn.clicked.connect(self.on_record_clicked)
        self.stop_btn.clicked.connect(self.on_stop_recording)
        self.start_all_btn.clicked.connect(self.on_start_all_recording)
        self.stop_all_btn.clicked.connect(self.on_stop_all_recording)
        self.preview_btn.clicked.connect(self.on_preview_clicked)
        self.preview_stop_btn.clicked.connect(self.on_preview_stop_clicked)
        
        # Connect to state manager signals
        self.viewmodel.state_manager.camera_connected.connect(self.on_camera_connected)
        self.viewmodel.state_manager.camera_disconnected.connect(self.on_camera_disconnected)
        
    def on_recording_started(self, camera_id):
        """녹화 시작됨"""
        self.ensure_camera_row(camera_id)
        self.update_camera_status(camera_id, "Recording", QColor(239, 68, 68))
        self.update_camera_time(camera_id, 0)
        self.update_camera_size(camera_id, 0)
        
        # Enable stop buttons when recording starts
        self.stop_btn.setEnabled(True)
        self.stop_all_btn.setEnabled(True)
        
    def on_recording_stopped(self, camera_id, file_path):
        """녹화 중지됨"""
        self.update_camera_status(camera_id, "Idle", QColor(148, 163, 184))
        self.update_camera_file(camera_id, file_path)
        
        # Check if any camera is still recording
        any_recording = False
        for row in range(self.status_table.rowCount()):
            status_item = self.status_table.item(row, 1)  # Status column
            if status_item and status_item.text() == "Recording":
                any_recording = True
                break
        
        # Disable stop buttons only if no camera is recording
        if not any_recording:
            self.stop_btn.setEnabled(False)
            self.stop_all_btn.setEnabled(False)
        
    def on_preview_started(self, camera_id):
        """프리뷰 시작됨"""
        self.ensure_camera_row(camera_id)
        self.update_camera_status(camera_id, "Preview", QColor(59, 130, 246))
        
    def on_preview_stopped(self, camera_id):
        """프리뷰 중지됨"""
        self.update_camera_status(camera_id, "Idle", QColor(148, 163, 184))
        
    def on_status_changed(self, camera_id, status):
        """상태 변경됨"""
        # Update camera list item
        for i in range(self.camera_list.count()):
            item = self.camera_list.item(i)
            if item.data(Qt.UserRole) == camera_id:
                item.setText(f"{camera_id} - {status.title()}")
                break
                
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
        
        
    def on_recording_time_updated(self, camera_id, seconds):
        """녹화 시간 업데이트"""
        self.update_camera_time(camera_id, seconds)
        
    def on_file_size_updated(self, camera_id, size_mb):
        """파일 크기 업데이트"""
        self.update_camera_size(camera_id, size_mb)
            
    def on_record_clicked(self):
        """녹화 버튼 클릭"""
        selected_items = self.camera_list.selectedItems()
        if not selected_items:
            self.on_error_occurred("Select camera(s) first")
            return
            
        if self.viewmodel:
            for item in selected_items:
                camera_id = item.data(Qt.UserRole)
                asyncio.create_task(self.viewmodel.start_recording(camera_id))
            
    def on_stop_recording(self):
        """녹화 정지"""
        selected_items = self.camera_list.selectedItems()
        if not selected_items:
            self.on_error_occurred("Select camera(s) first")
            return
            
        if self.viewmodel:
            for item in selected_items:
                camera_id = item.data(Qt.UserRole)
                asyncio.create_task(self.viewmodel.stop_recording(camera_id))
                
    def on_start_all_recording(self):
        """모든 카메라 녹화 시작"""
        if not self.viewmodel:
            return
            
        # Get connected cameras from state manager
        connected_cameras = self.viewmodel.get_connected_cameras()
        if not connected_cameras:
            self.on_error_occurred("No cameras connected")
            return
            
        # Get camera IDs that are not currently recording
        camera_ids = []
        for camera in connected_cameras:
            camera_id = camera.id
            if not self.viewmodel.is_recording(camera_id):
                camera_ids.append(camera_id)
                
        if not camera_ids:
            self.on_error_occurred("All cameras are already recording")
            return
            
        # Start recording on all cameras simultaneously
        asyncio.create_task(self.viewmodel.start_recording_many(camera_ids))
                
    def on_stop_all_recording(self):
        """모든 카메라 녹화 정지"""
        if not self.viewmodel:
            return
            
        # Get connected cameras from state manager
        connected_cameras = self.viewmodel.get_connected_cameras()
        if not connected_cameras:
            self.on_error_occurred("No cameras connected")
            return
            
        # Get camera IDs that are currently recording
        camera_ids = []
        for camera in connected_cameras:
            camera_id = camera.id
            if self.viewmodel.is_recording(camera_id):
                camera_ids.append(camera_id)
                
        if not camera_ids:
            self.on_error_occurred("No cameras are currently recording")
            return
            
        # Stop recording on all cameras simultaneously
        asyncio.create_task(self.viewmodel.stop_recording_many(camera_ids))
            
    def on_preview_clicked(self):
        """프리뷰 버튼 클릭"""
        current_item = self.camera_list.currentItem()
        if current_item and self.viewmodel:
            camera_id = current_item.data(Qt.UserRole)
            asyncio.create_task(self.viewmodel.start_preview(camera_id))
            
    def on_preview_stop_clicked(self):
        """프리뷰 중지 버튼 클릭"""
        current_item = self.camera_list.currentItem()
        if current_item and self.viewmodel:
            camera_id = current_item.data(Qt.UserRole)
            asyncio.create_task(self.viewmodel.stop_preview(camera_id))
            
    def update_camera_list(self, cameras):
        """카메라 목록 업데이트"""
        self.camera_list.clear()
        self.connected_cameras = []
        
        for camera in cameras:
            if camera.status.value == "connected":
                item = QListWidgetItem()
                item.setText(f"{camera.id} - {camera.name}")
                item.setData(Qt.UserRole, camera.id)
                self.camera_list.addItem(item)
                self.connected_cameras.append(camera.id)
                
    def on_camera_connected(self, camera_id, camera_info):
        """카메라 연결됨"""
        item = QListWidgetItem()
        item.setText(f"{camera_id} - {camera_info.name}")
        item.setData(Qt.UserRole, camera_id)
        self.camera_list.addItem(item)
        self.connected_cameras.append(camera_id)
        self.ensure_camera_row(camera_id)
        
    def on_camera_disconnected(self, camera_id):
        """카메라 연결 해제됨"""
        for i in range(self.camera_list.count()):
            item = self.camera_list.item(i)
            if item.data(Qt.UserRole) == camera_id:
                self.camera_list.takeItem(i)
                break
                
        if camera_id in self.connected_cameras:
            self.connected_cameras.remove(camera_id)
            
        self.remove_camera_row(camera_id)
        
    def on_start_preview(self):
        """프리뷰 시작"""
        self.preview_btn.setEnabled(False)
        self.preview_stop_btn.setEnabled(True)
        self.preview_label.setText("Preview starting...")
        
    def on_stop_preview(self):
        """프리뷰 정지"""
        self.preview_btn.setEnabled(True)
        self.preview_stop_btn.setEnabled(False)
        self.preview_label.setText("No preview available")
        
    def update_recording_time(self, seconds):
        """녹화 시간 업데이트"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        secs = seconds % 60
        self.time_label.setText(f"{hours:02d}:{minutes:02d}:{secs:02d}")
        
    def update_battery_level(self, level):
        """배터리 레벨 업데이트"""
        self.battery_label.setText(f"Battery: {level}%")
        
    def update_progress(self, progress):
        """진행률 업데이트"""
        self.progress_ring.set_progress(progress)
        
    def ensure_camera_row(self, camera_id):
        """카메라 행이 존재하는지 확인하고 없으면 생성"""
        if camera_id not in self.row_by_camera:
            row = self.status_table.rowCount()
            self.status_table.insertRow(row)
            self.row_by_camera[camera_id] = row
            
            # Initialize row with camera info
            self.status_table.setItem(row, 0, QTableWidgetItem(camera_id))
            self.status_table.setItem(row, 1, QTableWidgetItem("Idle"))
            self.status_table.setItem(row, 2, QTableWidgetItem("00:00:00"))
            self.status_table.setItem(row, 3, QTableWidgetItem("0"))
            self.status_table.setItem(row, 4, QTableWidgetItem(""))
            
            # Set idle color
            self.status_table.item(row, 1).setForeground(QColor(148, 163, 184))
            
    def update_camera_status(self, camera_id, status, color=None):
        """카메라 상태 업데이트"""
        if camera_id in self.row_by_camera:
            row = self.row_by_camera[camera_id]
            self.status_table.setItem(row, 1, QTableWidgetItem(status))
            if color:
                self.status_table.item(row, 1).setForeground(color)
                
    def update_camera_time(self, camera_id, seconds):
        """카메라 녹화 시간 업데이트"""
        if camera_id in self.row_by_camera:
            row = self.row_by_camera[camera_id]
            hours = seconds // 3600
            minutes = (seconds % 3600) // 60
            secs = seconds % 60
            self.status_table.setItem(row, 2, QTableWidgetItem(f"{hours:02d}:{minutes:02d}:{secs:02d}"))
            
    def update_camera_size(self, camera_id, size_mb):
        """카메라 파일 크기 업데이트"""
        if camera_id in self.row_by_camera:
            row = self.row_by_camera[camera_id]
            self.status_table.setItem(row, 3, QTableWidgetItem(str(size_mb)))
            
    def update_camera_file(self, camera_id, file_path):
        """카메라 파일 경로 업데이트"""
        if camera_id in self.row_by_camera:
            row = self.row_by_camera[camera_id]
            self.status_table.setItem(row, 4, QTableWidgetItem(file_path))
            
    def remove_camera_row(self, camera_id):
        """카메라 행 제거"""
        if camera_id in self.row_by_camera:
            row = self.row_by_camera[camera_id]
            self.status_table.removeRow(row)
            del self.row_by_camera[camera_id]
            
            # Update row mappings for remaining cameras
            for cid, old_row in list(self.row_by_camera.items()):
                if old_row > row:
                    self.row_by_camera[cid] = old_row - 1
