"""
Camera management view

Displays camera list, scan controls, and connection status
"""

import asyncio
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QTableView, QLabel, QFrame, QHeaderView, QAbstractItemView
)
from PySide6.QtCore import Qt, QAbstractTableModel, Signal, QTimer
from PySide6.QtGui import QFont

from ..widgets.glass_card import GlassCard
from ..widgets.neuro_button import NeuroButton
from ..widgets.progress_ring import ProgressRing, LoadingSpinner
from ..viewmodels.camera_vm import CameraViewModel
from ...core.models import CameraInfo, CameraStatus


class CameraTableModel(QAbstractTableModel):
    """Camera 리스트를 테이블에 표시하는 모델"""
    
    def __init__(self, cameras=None):
        super().__init__()
        self.cameras = cameras or []
        self.headers = ["ID", "Name", "Model", "Status", "Battery", "IP Address"]
        
    def rowCount(self, parent=None):
        return len(self.cameras)
        
    def columnCount(self, parent=None):
        return len(self.headers)
        
    def headerData(self, section, orientation, role=Qt.ItemDataRole.DisplayRole):
        if role == Qt.ItemDataRole.DisplayRole and orientation == Qt.Orientation.Horizontal:
            return self.headers[section]
        return None
        
    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= len(self.cameras):
            return None
            
        camera = self.cameras[index.row()]
        col = index.column()
        
        if role == Qt.ItemDataRole.DisplayRole:
            if col == 0: return camera.id
            elif col == 1: return camera.name
            elif col == 2: return camera.model
            elif col == 3: return camera.status.value.title()
            elif col == 4: return f"{camera.battery_level}%" if camera.battery_level > 0 else "N/A"
            elif col == 5: return "192.168.1.100"  # Mock IP address
            
        elif role == Qt.ItemDataRole.TextAlignmentRole:
            if col in [0, 4]:  # ID, Battery
                return Qt.AlignmentFlag.AlignCenter
            return Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter
            
        return None
        
    def update_cameras(self, cameras):
        """카메라 리스트 업데이트"""
        self.beginResetModel()
        self.cameras = cameras
        self.endResetModel()


class CameraView(QWidget):
    """카메라 관리 화면"""
    
    # Signals
    camera_selected = Signal(str)  # camera_id
    connect_requested = Signal(str)  # camera_id
    disconnect_requested = Signal(str)  # camera_id
    
    def __init__(self):
        super().__init__()
        self.viewmodel = None
        self.setup_ui()
        
        # Debounce timer for scan button
        self.scan_debounce_timer = QTimer()
        self.scan_debounce_timer.setSingleShot(True)
        self.scan_debounce_timer.timeout.connect(self.perform_scan)
        
        # Battery update timer
        self.battery_timer = QTimer()
        self.battery_timer.timeout.connect(self.update_battery_info)
        self.battery_timer.setInterval(5000)  # 5 seconds
        
    def setup_ui(self):
        """UI 구성"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)
        
        # Header
        header_card = GlassCard()
        
        # Add title
        title_label = QLabel("Camera Management")
        title_label.setStyleSheet("""
            QLabel {
                color: rgba(226, 232, 240, 1);
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 8px;
            }
        """)
        header_card.content_layout.addWidget(title_label)
        
        # Scan button
        self.scan_btn = NeuroButton("Scan for Cameras", "primary")
        self.scan_btn.clicked.connect(self.on_scan_clicked)
        header_card.content_layout.addWidget(self.scan_btn)
        
        # Loading spinner
        self.loading_spinner = LoadingSpinner(24)
        self.loading_spinner.hide()
        header_card.content_layout.addWidget(self.loading_spinner)
        
        header_card.content_layout.addStretch()
        
        # Status label
        self.status_label = QLabel("Ready to scan")
        self.status_label.setStyleSheet("""
            QLabel {
                color: rgba(148, 163, 184, 1);
                font-size: 14px;
                font-weight: 500;
            }
        """)
        header_card.content_layout.addWidget(self.status_label)
        
        layout.addWidget(header_card)
        
        # Camera table
        table_card = GlassCard("Detected Cameras")
        table_layout = table_card.createVerticalLayout()
        
        # Table
        self.table = QTableView()
        self.model = CameraTableModel()
        self.table.setModel(self.model)
        
        # Table styling
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setSelectionMode(QAbstractItemView.SingleSelection)
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.table.verticalHeader().setVisible(False)
        
        # Set minimum height to show at least 5 rows
        self.table.setMinimumHeight(200)
        self.table.setMaximumHeight(400)
        
        # Selection handling
        self.table.selectionModel().selectionChanged.connect(self.on_selection_changed)
        
        table_layout.addWidget(self.table)
        
        # Action buttons
        action_layout = QHBoxLayout()
        
        self.connect_btn = NeuroButton("Connect", "success")
        self.connect_btn.clicked.connect(self.on_connect_clicked)
        self.connect_btn.setEnabled(False)
        action_layout.addWidget(self.connect_btn)
        
        self.disconnect_btn = NeuroButton("Disconnect", "danger")
        self.disconnect_btn.clicked.connect(self.on_disconnect_clicked)
        self.disconnect_btn.setEnabled(False)
        action_layout.addWidget(self.disconnect_btn)
        
        # Bulk action buttons
        self.connect_all_btn = NeuroButton("Connect All", "primary")
        self.connect_all_btn.clicked.connect(self.on_connect_all_clicked)
        self.connect_all_btn.setEnabled(False)
        action_layout.addWidget(self.connect_all_btn)
        
        self.disconnect_all_btn = NeuroButton("Disconnect All", "secondary")
        self.disconnect_all_btn.clicked.connect(self.on_disconnect_all_clicked)
        self.disconnect_all_btn.setEnabled(False)
        action_layout.addWidget(self.disconnect_all_btn)
        
        action_layout.addStretch()
        
        table_layout.addLayout(action_layout)
        layout.addWidget(table_card)
        
        # Details panel (placeholder)
        details_card = GlassCard("Camera Details")
        details_layout = details_card.createVerticalLayout()
        
        self.details_label = QLabel("Select a camera to view details")
        self.details_label.setStyleSheet("""
            QLabel {
                color: rgba(148, 163, 184, 1);
                font-size: 14px;
                font-style: italic;
            }
        """)
        details_layout.addWidget(self.details_label)
        
        layout.addWidget(details_card)
        
    def set_viewmodel(self, vm):
        """ViewModel 주입"""
        self.viewmodel = vm
        if vm:
            # Connect signals
            vm.cameras_changed.connect(self.on_cameras_changed)
            vm.status_changed.connect(self.on_status_changed)
            vm.scan_started.connect(self.on_scan_started)
            vm.scan_finished.connect(self.on_scan_finished)
            vm.connection_started.connect(self.on_connection_started)
            vm.connection_finished.connect(self.on_connection_finished)
            vm.error_occurred.connect(self.on_error_occurred)
            
    def on_scan_clicked(self):
        """스캔 버튼 클릭"""
        if self.viewmodel:
            import asyncio
            asyncio.create_task(self.viewmodel.scan_cameras())
            
    def on_connect_clicked(self):
        """연결 버튼 클릭"""
        selection = self.table.selectionModel().selectedRows()
        if selection and self.viewmodel:
            camera_id = self.table_model.cameras[selection[0].row()].id
            import asyncio
            asyncio.create_task(self.viewmodel.connect_camera(camera_id))
            
    def on_disconnect_clicked(self):
        """연결 해제 버튼 클릭"""
        selection = self.table.selectionModel().selectedRows()
        if selection and self.viewmodel:
            camera_id = self.table_model.cameras[selection[0].row()].id
            import asyncio
            asyncio.create_task(self.viewmodel.disconnect_camera(camera_id))
            
    def on_selection_changed(self):
        """테이블 선택 변경"""
        selection = self.table.selectionModel().selectedRows()
        has_selection = len(selection) > 0
        
        self.connect_btn.setEnabled(has_selection)
        self.disconnect_btn.setEnabled(has_selection)
        
        # Bulk action buttons 상태 업데이트
        self.update_bulk_button_states()
        
        if has_selection:
            camera = self.model.cameras[selection[0].row()]
            self.details_label.setText(f"""
                <b>Camera Details:</b><br>
                ID: {camera.id}<br>
                Name: {camera.name}<br>
                Model: {camera.model}<br>
                Status: {camera.status.value.title()}<br>
                Battery: {camera.battery_level}%<br>
                IP: {camera.ip_address or 'N/A'}
            """)
        else:
            self.details_label.setText("Select a camera to view details")
            
    def on_cameras_changed(self, cameras):
        """ViewModel에서 카메라 리스트 변경 알림"""
        self.model.update_cameras(cameras)
        self.update_bulk_button_states()
        
    def on_status_changed(self, camera_id, status):
        """카메라 상태 변경"""
        # 테이블 모델 업데이트
        for i, camera in enumerate(self.model.cameras):
            if camera.id == camera_id:
                camera.status = CameraStatus(status)
                self.model.dataChanged.emit(
                    self.model.index(i, 3),
                    self.model.index(i, 3)
                )
                break
        self.update_bulk_button_states()
        
    def update_bulk_button_states(self):
        """Connect All, Disconnect All 버튼 상태 업데이트"""
        if not hasattr(self, 'model') or not self.model.cameras:
            self.connect_all_btn.setEnabled(False)
            self.disconnect_all_btn.setEnabled(False)
            return
            
        # 연결되지 않은 카메라가 있는지 확인
        has_disconnected = any(camera.status == CameraStatus.DISCONNECTED 
                             for camera in self.model.cameras)
        self.connect_all_btn.setEnabled(has_disconnected)
        
        # 연결된 카메라가 있는지 확인
        has_connected = any(camera.status == CameraStatus.CONNECTED 
                           for camera in self.model.cameras)
        self.disconnect_all_btn.setEnabled(has_connected)
                
    def on_scan_started(self):
        """스캔 시작"""
        self.scan_btn.setEnabled(False)
        self.loading_spinner.start_animation()
        self.loading_spinner.show()
        self.status_label.setText("Scanning for cameras...")
        
    def on_scan_finished(self, cameras):
        """스캔 완료"""
        self.scan_btn.setEnabled(True)
        self.loading_spinner.stop_animation()
        self.loading_spinner.hide()
        self.status_label.setText(f"Found {len(cameras)} cameras")
        
    def on_connection_started(self, camera_id):
        """연결 시작"""
        self.status_label.setText(f"Connecting to {camera_id}...")
        
    def on_connection_finished(self, camera_id, success):
        """연결 완료"""
        if success:
            self.status_label.setText(f"Connected to {camera_id}")
        else:
            self.status_label.setText(f"Failed to connect to {camera_id}")
            
    def on_error_occurred(self, error_message):
        """에러 발생"""
        self.status_label.setText(f"Error: {error_message}")
        self.scan_btn.setEnabled(True)
        self.loading_spinner.stop_animation()
        self.loading_spinner.hide()
        
    def set_viewmodel(self, viewmodel):
        """ViewModel 설정 및 이벤트 연결"""
        self.viewmodel = viewmodel
        
        # Connect signals
        self.viewmodel.cameras_changed.connect(self.on_cameras_changed)
        self.viewmodel.status_changed.connect(self.on_status_changed)
        self.viewmodel.scan_started.connect(self.on_scan_started)
        self.viewmodel.scan_finished.connect(self.on_scan_finished)
        self.viewmodel.connection_started.connect(self.on_connection_started)
        self.viewmodel.connection_finished.connect(self.on_connection_finished)
        self.viewmodel.error_occurred.connect(self.on_error_occurred)
        self.viewmodel.busy_changed.connect(self.on_busy_changed)
        
        # Connect button events with debounce
        self.scan_btn.clicked.connect(self.on_scan_clicked)
        self.connect_btn.clicked.connect(self.on_connect_clicked)
        self.disconnect_btn.clicked.connect(self.on_disconnect_clicked)
        
        # Start battery update timer
        self.battery_timer.start()
        
    def on_busy_changed(self, busy):
        """작업 중 상태 변경"""
        self.scan_btn.setEnabled(not busy)
        self.connect_btn.setEnabled(not busy)
        self.disconnect_btn.setEnabled(not busy)
        self.connect_all_btn.setEnabled(not busy)
        self.disconnect_all_btn.setEnabled(not busy)
        
    def on_connect_clicked(self):
        """Connect 버튼 클릭"""
        current_item = self.table.currentIndex()
        if current_item.isValid() and self.viewmodel:
            camera_id = self.model.cameras[current_item.row()].id
            asyncio.create_task(self.viewmodel.connect(camera_id))
            
    def on_disconnect_clicked(self):
        """Disconnect 버튼 클릭"""
        current_item = self.table.currentIndex()
        if current_item.isValid() and self.viewmodel:
            camera_id = self.model.cameras[current_item.row()].id
            asyncio.create_task(self.viewmodel.disconnect(camera_id))
            
    def on_connect_all_clicked(self):
        """Connect All 버튼 클릭"""
        if self.viewmodel and self.model.cameras:
            # 모든 연결되지 않은 카메라에 연결
            disconnected_cameras = [camera for camera in self.model.cameras 
                                   if camera.status == CameraStatus.DISCONNECTED]
            if disconnected_cameras:
                asyncio.create_task(self.viewmodel.connect_all(disconnected_cameras))
                
    def on_disconnect_all_clicked(self):
        """Disconnect All 버튼 클릭"""
        if self.viewmodel and self.model.cameras:
            # 모든 연결된 카메라에서 연결 해제
            connected_cameras = [camera for camera in self.model.cameras 
                               if camera.status == CameraStatus.CONNECTED]
            if connected_cameras:
                asyncio.create_task(self.viewmodel.disconnect_all(connected_cameras))
            
    def on_scan_clicked(self):
        """Scan 버튼 클릭 (디바운스 적용)"""
        if not self.scan_debounce_timer.isActive():
            self.scan_debounce_timer.start(500)  # 500ms debounce
            
    def perform_scan(self):
        """실제 스캔 수행"""
        if self.viewmodel:
            asyncio.create_task(self.viewmodel.scan())
            
    def update_battery_info(self):
        """배터리 정보 주기적 업데이트"""
        if self.viewmodel and not self.viewmodel.is_busy():
            # Mock 어댑터에서 배터리 정보 업데이트
            cameras = self.viewmodel.get_all_cameras()
            for camera in cameras:
                if camera.status.value == "connected":
                    # Mock에서 배터리 레벨 랜덤 업데이트
                    import random
                    camera.battery_level = max(10, camera.battery_level - random.randint(0, 2))
                    
            # UI 업데이트
            self.model.update_cameras(cameras)
