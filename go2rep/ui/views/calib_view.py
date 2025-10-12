"""
Camera calibration view

Provides intrinsic and extrinsic calibration controls
"""

import asyncio
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QLabel, QFrame, QComboBox, QSpinBox, QCheckBox,
    QGroupBox, QGridLayout, QSlider, QProgressBar,
    QTabWidget, QTextEdit, QFileDialog, QListWidget,
    QTableWidget, QTableWidgetItem, QHeaderView, QAbstractItemView,
    QLineEdit, QSplitter
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QFont

from ..widgets.glass_card import GlassCard, NeuroCard
from ..widgets.neuro_button import NeuroButton
from ..widgets.progress_ring import ProgressRing, LoadingSpinner
from ..widgets.file_list import FileListWidget
from ..viewmodels.calib_vm import CalibViewModel


class CalibView(QWidget):
    """카메라 캘리브레이션 화면"""
    
    # Signals
    calibration_started = Signal(str)  # calib_type
    calibration_finished = Signal(str, bool)  # calib_type, success
    image_selected = Signal(str)  # image_path
    
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
        title_label = QLabel("Camera Calibration")
        title_label.setStyleSheet("""
            QLabel {
                color: rgba(226, 232, 240, 1);
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 8px;
            }
        """)
        header_card.content_layout.addWidget(title_label)
        
        # Calibration status
        self.status_label = QLabel("Ready to calibrate")
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
        
        # Left panel - Image management
        image_card = GlassCard("Calibration Images")
        image_layout = image_card.createVerticalLayout()
        
        # Image list widget
        self.image_list_widget = FileListWidget()
        self.image_list_widget.setMaximumHeight(200)
        image_layout.addWidget(self.image_list_widget)
        
        # Image management buttons
        image_buttons = QHBoxLayout()
        
        self.add_images_btn = NeuroButton("Add Images", "primary")
        self.remove_image_btn = NeuroButton("Remove", "secondary")
        self.clear_images_btn = NeuroButton("Clear All", "danger")
        
        image_buttons.addWidget(self.add_images_btn)
        image_buttons.addWidget(self.remove_image_btn)
        image_buttons.addWidget(self.clear_images_btn)
        
        image_layout.addLayout(image_buttons)
        
        # Image details
        details_group = QGroupBox("Image Details")
        details_layout = QVBoxLayout(details_group)
        details_layout.setContentsMargins(16, 16, 16, 16)
        
        # Image info
        self.image_info_label = QLabel("No image selected")
        self.image_info_label.setStyleSheet("""
            QLabel {
                color: rgba(226, 232, 240, 0.7);
                font-size: 14px;
            }
        """)
        details_layout.addWidget(self.image_info_label)
        
        # Quality score
        quality_layout = QHBoxLayout()
        quality_layout.addWidget(QLabel("Quality Score:"))
        self.quality_label = QLabel("N/A")
        self.quality_label.setStyleSheet("""
            QLabel {
                color: rgba(34, 197, 94, 1);
                font-weight: bold;
            }
        """)
        quality_layout.addWidget(self.quality_label)
        details_layout.addLayout(quality_layout)
        
        # Corner detection status
        corner_layout = QHBoxLayout()
        corner_layout.addWidget(QLabel("Corners Detected:"))
        self.corner_label = QLabel("No")
        self.corner_label.setStyleSheet("""
            QLabel {
                color: rgba(239, 68, 68, 1);
                font-weight: bold;
            }
        """)
        corner_layout.addWidget(self.corner_label)
        details_layout.addLayout(corner_layout)
        
        image_layout.addWidget(details_group)
        
        main_layout.addWidget(image_card)
        
        # Right panel - Calibration controls
        controls_card = GlassCard("Calibration Controls")
        controls_layout = controls_card.createVerticalLayout()
        
        # Tab widget for different calibration types
        self.tab_widget = QTabWidget()
        
        # Intrinsic calibration tab
        self.intrinsic_tab = self.create_intrinsic_tab()
        self.tab_widget.addTab(self.intrinsic_tab, "Intrinsic")
        
        # Extrinsic calibration tab
        self.extrinsic_tab = self.create_extrinsic_tab()
        self.tab_widget.addTab(self.extrinsic_tab, "Extrinsic")
        
        controls_layout.addWidget(self.tab_widget)
        
        # Calibration buttons
        calib_buttons = QVBoxLayout()
        
        self.start_intrinsic_btn = NeuroButton("Start Intrinsic Calibration", "primary")
        self.start_extrinsic_btn = NeuroButton("Start Extrinsic Calibration", "primary")
        self.cancel_calib_btn = NeuroButton("Cancel", "secondary")
        self.cancel_calib_btn.setEnabled(False)
        
        calib_buttons.addWidget(self.start_intrinsic_btn)
        calib_buttons.addWidget(self.start_extrinsic_btn)
        calib_buttons.addWidget(self.cancel_calib_btn)
        
        controls_layout.addLayout(calib_buttons)
        
        main_layout.addWidget(controls_card)
        
        layout.addLayout(main_layout)
        
        # Results panel
        results_card = GlassCard("Calibration Results")
        results_layout = results_card.createVerticalLayout()
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["Parameter", "Value", "Unit"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.results_table.setMaximumHeight(150)
        results_layout.addWidget(self.results_table)
        
        # Results text
        self.results_text = QTextEdit()
        self.results_text.setMaximumHeight(100)
        self.results_text.setPlaceholderText("Detailed calibration results will appear here...")
        results_layout.addWidget(self.results_text)
        
        layout.addWidget(results_card)
        
    def create_intrinsic_tab(self):
        """Intrinsic 캘리브레이션 탭 생성"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Chessboard settings
        chessboard_group = QGroupBox("Chessboard Settings")
        chessboard_layout = QGridLayout(chessboard_group)
        chessboard_layout.setContentsMargins(16, 16, 16, 16)
        chessboard_layout.setSpacing(10)
        
        # Board size
        chessboard_layout.addWidget(QLabel("Board Size:"), 0, 0)
        self.board_width_spinbox = QSpinBox()
        self.board_width_spinbox.setRange(3, 20)
        self.board_width_spinbox.setValue(9)
        chessboard_layout.addWidget(self.board_width_spinbox, 0, 1)
        
        chessboard_layout.addWidget(QLabel("x"), 0, 2)
        self.board_height_spinbox = QSpinBox()
        self.board_height_spinbox.setRange(3, 20)
        self.board_height_spinbox.setValue(6)
        chessboard_layout.addWidget(self.board_height_spinbox, 0, 3)
        
        # Square size
        chessboard_layout.addWidget(QLabel("Square Size (mm):"), 1, 0)
        self.square_size_spinbox = QSpinBox()
        self.square_size_spinbox.setRange(1, 100)
        self.square_size_spinbox.setValue(25)
        chessboard_layout.addWidget(self.square_size_spinbox, 1, 1)
        
        layout.addWidget(chessboard_group)
        
        # Calibration options
        options_group = QGroupBox("Calibration Options")
        options_layout = QVBoxLayout(options_group)
        options_layout.setContentsMargins(16, 16, 16, 16)
        
        self.auto_detect_corners_cb = QCheckBox("Auto-detect corners")
        self.auto_detect_corners_cb.setChecked(True)
        options_layout.addWidget(self.auto_detect_corners_cb)
        
        self.refine_corners_cb = QCheckBox("Refine corner detection")
        self.refine_corners_cb.setChecked(True)
        options_layout.addWidget(self.refine_corners_cb)
        
        self.calculate_distortion_cb = QCheckBox("Calculate distortion coefficients")
        self.calculate_distortion_cb.setChecked(True)
        options_layout.addWidget(self.calculate_distortion_cb)
        
        layout.addWidget(options_group)
        
        return tab
        
    def create_extrinsic_tab(self):
        """Extrinsic 캘리브레이션 탭 생성"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)
        
        # Camera setup
        camera_group = QGroupBox("Camera Setup")
        camera_layout = QGridLayout(camera_group)
        camera_layout.setContentsMargins(16, 16, 16, 16)
        camera_layout.setSpacing(10)
        
        # Number of cameras
        camera_layout.addWidget(QLabel("Number of Cameras:"), 0, 0)
        self.num_cameras_spinbox = QSpinBox()
        self.num_cameras_spinbox.setRange(2, 10)
        self.num_cameras_spinbox.setValue(3)
        camera_layout.addWidget(self.num_cameras_spinbox, 0, 1)
        
        # Calibration method
        camera_layout.addWidget(QLabel("Method:"), 1, 0)
        self.method_combo = QComboBox()
        self.method_combo.addItems(["Stereo", "Multi-camera", "Bundle Adjustment"])
        camera_layout.addWidget(self.method_combo, 1, 1)
        
        layout.addWidget(camera_group)
        
        # Calibration options
        options_group = QGroupBox("Calibration Options")
        options_layout = QVBoxLayout(options_group)
        options_layout.setContentsMargins(16, 16, 16, 16)
        
        self.estimate_poses_cb = QCheckBox("Estimate camera poses")
        self.estimate_poses_cb.setChecked(True)
        options_layout.addWidget(self.estimate_poses_cb)
        
        self.optimize_positions_cb = QCheckBox("Optimize camera positions")
        self.optimize_positions_cb.setChecked(True)
        options_layout.addWidget(self.optimize_positions_cb)
        
        self.validate_calibration_cb = QCheckBox("Validate calibration")
        self.validate_calibration_cb.setChecked(True)
        options_layout.addWidget(self.validate_calibration_cb)
        
        layout.addWidget(options_group)
        
        return tab
        
    def set_viewmodel(self, viewmodel):
        """ViewModel 설정 및 이벤트 연결"""
        self.viewmodel = viewmodel
        
        # Connect signals
        self.viewmodel.images_changed.connect(self.on_images_changed)
        self.viewmodel.calibration_started.connect(self.on_calibration_started)
        self.viewmodel.calibration_progress.connect(self.on_calibration_progress)
        self.viewmodel.calibration_finished.connect(self.on_calibration_finished)
        self.viewmodel.calibration_result.connect(self.on_calibration_result)
        self.viewmodel.error_occurred.connect(self.on_error_occurred)
        self.viewmodel.busy_changed.connect(self.on_busy_changed)
        
        # Connect button events
        self.add_images_btn.clicked.connect(self.on_add_images_clicked)
        self.remove_image_btn.clicked.connect(self.on_remove_image_clicked)
        self.clear_images_btn.clicked.connect(self.on_clear_images_clicked)
        self.start_intrinsic_btn.clicked.connect(self.on_start_intrinsic_clicked)
        self.start_extrinsic_btn.clicked.connect(self.on_start_extrinsic_clicked)
        self.cancel_calib_btn.clicked.connect(self.on_cancel_calib_clicked)
        
        # Connect list selection
        self.image_list_widget.itemSelectionChanged.connect(self.on_image_selected)
        
    def on_images_changed(self, images):
        """이미지 목록 변경됨"""
        self.image_list_widget.update_files(images)
        
    def on_image_selected(self):
        """이미지 선택됨"""
        selected_files = self.image_list_widget.get_selected_files()
        if selected_files:
            image_path = selected_files[0]
            
            # Find image info
            images = self.viewmodel.get_images()
            for img in images:
                if img["path"] == image_path:
                    # Update image details
                    self.image_info_label.setText(f"Selected: {img['name']}")
                    
                    # Update quality score
                    if img["quality_score"] > 0:
                        self.quality_label.setText(f"{img['quality_score']:.2f}")
                        self.quality_label.setStyleSheet("""
                            QLabel {
                                color: rgba(34, 197, 94, 1);
                                font-weight: bold;
                            }
                        """)
                    else:
                        self.quality_label.setText("N/A")
                        self.quality_label.setStyleSheet("""
                            QLabel {
                                color: rgba(239, 68, 68, 1);
                                font-weight: bold;
                            }
                        """)
                    
                    # Update corner detection status
                    if img["corners_detected"]:
                        self.corner_label.setText("Yes")
                        self.corner_label.setStyleSheet("""
                            QLabel {
                                color: rgba(34, 197, 94, 1);
                                font-weight: bold;
                            }
                        """)
                    else:
                        self.corner_label.setText("No")
                        self.corner_label.setStyleSheet("""
                            QLabel {
                                color: rgba(239, 68, 68, 1);
                                font-weight: bold;
                            }
                        """)
                    break
                    
    def on_calibration_started(self, calib_type):
        """캘리브레이션 시작됨"""
        self.status_label.setText(f"{calib_type.title()} calibration started...")
        self.status_label.setStyleSheet("""
            QLabel {
                color: rgba(59, 130, 246, 1);
                font-size: 16px;
                font-weight: 600;
            }
        """)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
    def on_calibration_progress(self, progress):
        """캘리브레이션 진행률 업데이트"""
        self.progress_bar.setValue(progress)
        
    def on_calibration_finished(self, calib_type, success):
        """캘리브레이션 완료됨"""
        if success:
            self.status_label.setText(f"{calib_type.title()} calibration completed successfully")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: rgba(34, 197, 94, 1);
                    font-size: 16px;
                    font-weight: 600;
                }
            """)
        else:
            self.status_label.setText(f"{calib_type.title()} calibration failed")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: rgba(239, 68, 68, 1);
                    font-size: 16px;
                    font-weight: 600;
                }
            """)
            
        self.progress_bar.setVisible(False)
        
    def on_calibration_result(self, results):
        """캘리브레이션 결과 업데이트"""
        # Update results table
        if results["calib_type"] == "intrinsic":
            self.results_table.setRowCount(6)
            
            # Camera matrix
            camera_matrix = results["camera_matrix"]
            self.results_table.setItem(0, 0, QTableWidgetItem("Focal Length X"))
            self.results_table.setItem(0, 1, QTableWidgetItem(f"{camera_matrix['fx']:.2f}"))
            self.results_table.setItem(0, 2, QTableWidgetItem("pixels"))
            
            self.results_table.setItem(1, 0, QTableWidgetItem("Focal Length Y"))
            self.results_table.setItem(1, 1, QTableWidgetItem(f"{camera_matrix['fy']:.2f}"))
            self.results_table.setItem(1, 2, QTableWidgetItem("pixels"))
            
            self.results_table.setItem(2, 0, QTableWidgetItem("Principal Point X"))
            self.results_table.setItem(2, 1, QTableWidgetItem(f"{camera_matrix['cx']:.2f}"))
            self.results_table.setItem(2, 2, QTableWidgetItem("pixels"))
            
            self.results_table.setItem(3, 0, QTableWidgetItem("Principal Point Y"))
            self.results_table.setItem(3, 1, QTableWidgetItem(f"{camera_matrix['cy']:.2f}"))
            self.results_table.setItem(3, 2, QTableWidgetItem("pixels"))
            
            # Distortion coefficients
            distortion = results["distortion_coeffs"]
            self.results_table.setItem(4, 0, QTableWidgetItem("Radial Distortion K1"))
            self.results_table.setItem(4, 1, QTableWidgetItem(f"{distortion['k1']:.4f}"))
            self.results_table.setItem(4, 2, QTableWidgetItem(""))
            
            self.results_table.setItem(5, 0, QTableWidgetItem("Radial Distortion K2"))
            self.results_table.setItem(5, 1, QTableWidgetItem(f"{distortion['k2']:.4f}"))
            self.results_table.setItem(5, 2, QTableWidgetItem(""))
            
        elif results["calib_type"] == "extrinsic":
            self.results_table.setRowCount(len(results["camera_poses"]))
            
            for i, pose in enumerate(results["camera_poses"]):
                self.results_table.setItem(i, 0, QTableWidgetItem(f"Camera {pose['camera_id']}"))
                self.results_table.setItem(i, 1, QTableWidgetItem(f"Position: {pose['position']}"))
                self.results_table.setItem(i, 2, QTableWidgetItem(f"Rotation: {pose['rotation']}"))
                
        # Update results text
        result_text = f"""
Calibration Results:
- Type: {results['calib_type']}
- Reprojection Error: {results['reprojection_error']:.3f}
- Total Images: {results.get('total_images', results.get('total_cameras', 0))}
- Valid Images: {results.get('valid_images', results.get('total_cameras', 0))}
- Output: {results['output_path']}
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
        self.add_images_btn.setEnabled(not busy)
        self.remove_image_btn.setEnabled(not busy)
        self.clear_images_btn.setEnabled(not busy)
        self.start_intrinsic_btn.setEnabled(not busy)
        self.start_extrinsic_btn.setEnabled(not busy)
        self.cancel_calib_btn.setEnabled(busy)
        
    def on_add_images_clicked(self):
        """이미지 추가 버튼 클릭"""
        file_paths, _ = QFileDialog.getOpenFileNames(
            self, "Select Calibration Images", "", "Image Files (*.jpg *.jpeg *.png *.bmp)"
        )
        
        for file_path in file_paths:
            self.viewmodel.add_image(file_path)
            
    def on_remove_image_clicked(self):
        """이미지 제거 버튼 클릭"""
        selected_files = self.image_list_widget.get_selected_files()
        for file_path in selected_files:
            self.viewmodel.remove_image(file_path)
            
    def on_clear_images_clicked(self):
        """모든 이미지 제거 버튼 클릭"""
        self.viewmodel.clear_images()
        
    def on_start_intrinsic_clicked(self):
        """Intrinsic 캘리브레이션 시작 버튼 클릭"""
        asyncio.create_task(self.viewmodel.start_intrinsic_calibration())
        
    def on_start_extrinsic_clicked(self):
        """Extrinsic 캘리브레이션 시작 버튼 클릭"""
        asyncio.create_task(self.viewmodel.start_extrinsic_calibration())
        
    def on_cancel_calib_clicked(self):
        """캘리브레이션 취소 버튼 클릭"""
        self.viewmodel.cancel_calibration()