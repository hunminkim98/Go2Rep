"""
Download view

Provides GoPro video download interface with file listing, progress tracking, and bulk operations.
"""

import asyncio
import subprocess
import platform
from pathlib import Path
from typing import List, Dict
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QFrame, QComboBox, QSpinBox, QCheckBox,
    QGroupBox, QGridLayout, QSlider, QProgressBar,
    QTabWidget, QTextEdit, QFileDialog, QListWidget, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QLineEdit, QSplitter, QTreeWidget, QTreeWidgetItem
)
from PySide6.QtCore import Qt, Signal, QTimer
from PySide6.QtGui import QFont, QColor

from ..widgets.glass_card import GlassCard, NeuroCard
from ..widgets.neuro_button import NeuroButton
from ..widgets.progress_ring import ProgressRing, LoadingSpinner
from ..widgets.file_list import FileListWidget
from ..viewmodels.download_vm import DownloadViewModel


class DownloadView(QWidget):
    """GoPro 비디오 다운로드 화면"""
    
    # Signals
    download_started = Signal(str, str)  # camera_id, filename
    download_finished = Signal(str, str, str)  # camera_id, filename, result_path
    
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
        title_label = QLabel("Video Downloads")
        title_label.setStyleSheet("""
            QLabel {
                color: rgba(226, 232, 240, 1);
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 8px;
            }
        """)
        header_card.content_layout.addWidget(title_label)
        
        # Download status
        self.status_label = QLabel("Ready to download")
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
        
        # Left panel - Camera and file listing
        left_card = GlassCard("Connected Cameras & Files")
        left_layout = left_card.createVerticalLayout()
        
        # Camera list
        self.camera_list = QListWidget()
        self.camera_list.setMaximumHeight(150)
        self.camera_list.setSelectionMode(QAbstractItemView.SingleSelection)
        left_layout.addWidget(QLabel("Connected Cameras:"))
        left_layout.addWidget(self.camera_list)
        
        # File list
        self.file_list = QTreeWidget()
        self.file_list.setHeaderLabels(["Name", "Size", "Date"])
        self.file_list.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.file_list.setMaximumHeight(300)
        self.file_list.setStyleSheet("""
            QTreeWidget {
                background-color: rgba(21, 21, 21, 0.9);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                color: rgba(226, 232, 240, 1);
                font-size: 12px;
            }
            QTreeWidget::item {
                padding: 4px;
                border: none;
            }
            QTreeWidget::item:selected {
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
        left_layout.addWidget(QLabel("Available Files:"))
        left_layout.addWidget(self.file_list)
        
        # Camera status info
        camera_info_layout = QHBoxLayout()
        
        self.camera_count_label = QLabel("Connected Cameras: 0")
        self.camera_count_label.setStyleSheet("""
            QLabel {
                color: rgba(148, 163, 184, 1);
                font-size: 14px;
                font-weight: 600;
            }
        """)
        camera_info_layout.addWidget(self.camera_count_label)
        camera_info_layout.addStretch()
        
        left_layout.addLayout(camera_info_layout)
        
        # File actions
        file_actions = QHBoxLayout()
        
        self.scan_btn = NeuroButton("Scan Files", "primary")
        self.download_selected_btn = NeuroButton("Download Selected", "success")
        self.download_all_btn = NeuroButton("Download All", "success")
        
        file_actions.addWidget(self.scan_btn)
        file_actions.addWidget(self.download_selected_btn)
        file_actions.addWidget(self.download_all_btn)
        
        left_layout.addLayout(file_actions)
        
        main_layout.addWidget(left_card)
        
        # Right panel - Download controls and progress
        right_card = GlassCard("Download Controls & Progress")
        right_layout = right_card.createVerticalLayout()
        
        # Download options
        options_group = QGroupBox("Download Options")
        options_layout = QVBoxLayout(options_group)
        options_layout.setContentsMargins(16, 16, 16, 16)
        
        # Skip existing files
        self.skip_existing_cb = QCheckBox("Skip existing files")
        self.skip_existing_cb.setChecked(True)
        options_layout.addWidget(self.skip_existing_cb)
        
        # Overwrite existing files
        self.overwrite_cb = QCheckBox("Overwrite existing files")
        options_layout.addWidget(self.overwrite_cb)
        
        right_layout.addWidget(options_group)
        
        # Download actions
        download_actions = QVBoxLayout()
        
        self.open_folder_btn = NeuroButton("Open Download Folder", "secondary")
        
        download_actions.addWidget(self.open_folder_btn)
        
        right_layout.addLayout(download_actions)
        
        # Download progress table
        self.progress_table = QTableWidget()
        self.progress_table.setColumnCount(5)
        self.progress_table.setHorizontalHeaderLabels(["Camera", "File", "Progress (%)", "Speed", "Status"])
        self.progress_table.horizontalHeader().setStretchLastSection(True)
        self.progress_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.progress_table.verticalHeader().setVisible(False)
        self.progress_table.setAlternatingRowColors(True)
        self.progress_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.progress_table.setMinimumHeight(200)
        self.progress_table.setMaximumHeight(400)
        self.progress_table.setStyleSheet("""
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
        right_layout.addWidget(QLabel("Download Progress:"))
        right_layout.addWidget(self.progress_table)
        
        main_layout.addWidget(right_card)
        
        layout.addLayout(main_layout)
        
    def set_viewmodel(self, viewmodel):
        """ViewModel 설정 및 이벤트 연결"""
        self.viewmodel = viewmodel
        
        # Connect signals
        self.viewmodel.files_changed.connect(self.on_files_changed)
        self.viewmodel.download_started.connect(self.on_download_started)
        self.viewmodel.download_progress.connect(self.on_download_progress)
        self.viewmodel.download_finished.connect(self.on_download_finished)
        self.viewmodel.download_failed.connect(self.on_download_failed)
        self.viewmodel.error_occurred.connect(self.on_error_occurred)
        self.viewmodel.busy_changed.connect(self.on_busy_changed)
        
        # Connect button events
        self.scan_btn.clicked.connect(self.on_scan_clicked)
        self.download_selected_btn.clicked.connect(self.on_download_selected_clicked)
        self.download_all_btn.clicked.connect(self.on_download_all_clicked)
        self.open_folder_btn.clicked.connect(self.on_open_folder_clicked)
        
        # Connect list selection
        self.camera_list.currentItemChanged.connect(self.on_camera_selected)
        
        # Connect to state manager signals
        self.viewmodel.state_manager.camera_connected.connect(self.on_camera_connected)
        self.viewmodel.state_manager.camera_disconnected.connect(self.on_camera_disconnected)
        
        # Load already connected cameras
        self.load_connected_cameras()
        
        # Update camera count
        self.update_camera_count()
        
    def load_connected_cameras(self):
        """이미 연결된 카메라들을 로드"""
        connected_cameras = self.viewmodel.get_connected_cameras()
        
        for camera_id in connected_cameras:
            # Get camera info from state manager
            camera_info = self.viewmodel.state_manager.get_camera_info(camera_id)
            if camera_info:
                item = QListWidgetItem(f"{camera_id} - {camera_info.name}")
                item.setData(Qt.UserRole, camera_id)
                self.camera_list.addItem(item)
        
    def on_camera_connected(self, camera_id: str, camera_info):
        """카메라 연결됨"""
        # Check if camera already exists in list
        for i in range(self.camera_list.count()):
            item = self.camera_list.item(i)
            if item.data(Qt.UserRole) == camera_id:
                # Update existing item
                item.setText(f"{camera_id} - {camera_info.name}")
                return
        
        # Add new camera to list
        item = QListWidgetItem(f"{camera_id} - {camera_info.name}")
        item.setData(Qt.UserRole, camera_id)
        self.camera_list.addItem(item)
        
        # Update camera count
        self.update_camera_count()
        
    def on_camera_disconnected(self, camera_id: str):
        """카메라 연결 해제됨"""
        # Remove camera from list
        for i in range(self.camera_list.count()):
            item = self.camera_list.item(i)
            if item.data(Qt.UserRole) == camera_id:
                self.camera_list.takeItem(i)
                break
        
        # Clear files for this camera
        self.file_list.clear()
        
        # Update camera count
        self.update_camera_count()
        
    def on_camera_selected(self, current, previous):
        """카메라 선택됨"""
        if current:
            camera_id = current.data(Qt.UserRole)
            # Load files for selected camera
            files = self.viewmodel.get_files(camera_id)
            self.update_file_list(files)
            
    def on_files_changed(self, camera_id: str, files: List[Dict]):
        """파일 목록 변경됨"""
        # Update file list if this camera is selected
        current_item = self.camera_list.currentItem()
        if current_item and current_item.data(Qt.UserRole) == camera_id:
            self.update_file_list(files)
            
    def update_file_list(self, files: List[Dict]):
        """파일 목록 업데이트"""
        self.file_list.clear()
        
        for file in files:
            item = QTreeWidgetItem([
                file["name"],
                self.format_file_size(file["size"]),
                file["date"]
            ])
            item.setData(0, Qt.UserRole, file)
            self.file_list.addTopLevelItem(item)
            
    def format_file_size(self, size_bytes: int) -> str:
        """파일 크기 포맷팅"""
        if size_bytes < 1024:
            return f"{size_bytes} B"
        elif size_bytes < 1024 * 1024:
            return f"{size_bytes / 1024:.1f} KB"
        elif size_bytes < 1024 * 1024 * 1024:
            return f"{size_bytes / (1024 * 1024):.1f} MB"
        else:
            return f"{size_bytes / (1024 * 1024 * 1024):.1f} GB"
            
    def on_download_started(self, camera_id: str, filename: str):
        """다운로드 시작됨"""
        self.ensure_progress_row(camera_id, filename)
        self.update_progress_status(camera_id, filename, "Starting...")
        
    def on_download_progress(self, camera_id: str, filename: str, progress: int):
        """다운로드 진행률 업데이트"""
        self.update_progress_value(camera_id, filename, progress)
        self.update_progress_status(camera_id, filename, f"Downloading... {progress}%")
        
    def on_download_finished(self, camera_id: str, filename: str, result_path: str):
        """다운로드 완료됨"""
        self.update_progress_value(camera_id, filename, 100)
        self.update_progress_status(camera_id, filename, f"Completed: {result_path}")
        
    def on_download_failed(self, camera_id: str, filename: str, error: str):
        """다운로드 실패됨"""
        self.update_progress_status(camera_id, filename, f"Failed: {error}")
        
    def on_error_occurred(self, error_message: str):
        """에러 발생"""
        self.status_label.setText(f"Error: {error_message}")
        self.status_label.setStyleSheet("""
            QLabel {
                color: rgba(239, 68, 68, 1);
                font-size: 16px;
                font-weight: 600;
            }
        """)
        
    def on_busy_changed(self, busy: bool):
        """작업 중 상태 변경"""
        self.scan_btn.setEnabled(not busy)
        self.download_selected_btn.setEnabled(not busy)
        self.download_all_btn.setEnabled(not busy)
        
    def ensure_progress_row(self, camera_id: str, filename: str):
        """진행률 테이블에 행이 있는지 확인"""
        for row in range(self.progress_table.rowCount()):
            camera_item = self.progress_table.item(row, 0)
            file_item = self.progress_table.item(row, 1)
            if (camera_item and file_item and 
                camera_item.text() == camera_id and file_item.text() == filename):
                return
                
        # Add new row
        row = self.progress_table.rowCount()
        self.progress_table.insertRow(row)
        
        self.progress_table.setItem(row, 0, QTableWidgetItem(camera_id))
        self.progress_table.setItem(row, 1, QTableWidgetItem(filename))
        self.progress_table.setItem(row, 2, QTableWidgetItem("0"))
        self.progress_table.setItem(row, 3, QTableWidgetItem(""))
        self.progress_table.setItem(row, 4, QTableWidgetItem(""))
        
    def update_progress_value(self, camera_id: str, filename: str, progress: int):
        """진행률 값 업데이트"""
        for row in range(self.progress_table.rowCount()):
            camera_item = self.progress_table.item(row, 0)
            file_item = self.progress_table.item(row, 1)
            if (camera_item and file_item and 
                camera_item.text() == camera_id and file_item.text() == filename):
                progress_item = self.progress_table.item(row, 2)
                if progress_item:
                    progress_item.setText(str(progress))
                break
                
    def update_progress_status(self, camera_id: str, filename: str, status: str):
        """진행률 상태 업데이트"""
        for row in range(self.progress_table.rowCount()):
            camera_item = self.progress_table.item(row, 0)
            file_item = self.progress_table.item(row, 1)
            if (camera_item and file_item and 
                camera_item.text() == camera_id and file_item.text() == filename):
                status_item = self.progress_table.item(row, 4)
                if status_item:
                    status_item.setText(status)
                break
                
    def on_scan_clicked(self):
        """스캔 버튼 클릭"""
        current_item = self.camera_list.currentItem()
        if current_item:
            camera_id = current_item.data(Qt.UserRole)
            asyncio.create_task(self.viewmodel.scan_files(camera_id))
            
    def on_download_selected_clicked(self):
        """선택된 파일 다운로드 버튼 클릭"""
        current_item = self.camera_list.currentItem()
        if not current_item:
            return
            
        camera_id = current_item.data(Qt.UserRole)
        selected_items = self.file_list.selectedItems()
        
        if not selected_items:
            self.on_error_occurred("No files selected")
            return
            
        # Get selected files
        selected_files = []
        for item in selected_items:
            file_data = item.data(0, Qt.UserRole)
            if file_data:
                selected_files.append(file_data)
                
        if selected_files:
            asyncio.create_task(self.viewmodel.download_selected(camera_id, selected_files))
            
    def on_download_all_clicked(self):
        """모든 파일 다운로드 버튼 클릭"""
        current_item = self.camera_list.currentItem()
        if current_item:
            camera_id = current_item.data(Qt.UserRole)
            asyncio.create_task(self.viewmodel.download_all(camera_id))
            
    def on_download_all_cameras_clicked(self):
        """모든 카메라 다운로드 버튼 클릭"""
        asyncio.create_task(self.viewmodel.download_all_cameras())
        
    def on_cancel_clicked(self):
        """취소 버튼 클릭"""
        current_item = self.camera_list.currentItem()
        if current_item:
            camera_id = current_item.data(Qt.UserRole)
            self.viewmodel.cancel_downloads(camera_id)
        else:
            self.viewmodel.cancel_all_downloads()
            
    def on_open_folder_clicked(self):
        """폴더 열기 버튼 클릭"""
        current_item = self.camera_list.currentItem()
        if current_item:
            camera_id = current_item.data(Qt.UserRole)
            download_path = self.viewmodel.get_download_path(camera_id)
            
            # Open folder in system file manager
            if platform.system() == "Darwin":  # macOS
                subprocess.run(["open", str(download_path)])
            elif platform.system() == "Windows":
                subprocess.run(["explorer", str(download_path)])
            else:  # Linux
                subprocess.run(["xdg-open", str(download_path)])
        else:
            # Open general downloads folder
            from os.path import expanduser
            general_path = Path(expanduser('~')) / 'PerforMetrics' / 'Downloads'
            general_path.mkdir(parents=True, exist_ok=True)
            
            if platform.system() == "Darwin":  # macOS
                subprocess.run(["open", str(general_path)])
            elif platform.system() == "Windows":
                subprocess.run(["explorer", str(general_path)])
            else:  # Linux
                subprocess.run(["xdg-open", str(general_path)])
                
                
    def update_camera_count(self):
        """연결된 카메라 개수 업데이트"""
        count = self.camera_list.count()
        self.camera_count_label.setText(f"Connected Cameras: {count}")
