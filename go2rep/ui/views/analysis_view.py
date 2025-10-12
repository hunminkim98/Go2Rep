"""
Analysis view

Provides pose estimation, triangulation, and tracking controls
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
from ..viewmodels.analysis_vm import AnalysisViewModel


class AnalysisView(QWidget):
    """분석 화면"""
    
    # Signals
    analysis_started = Signal(str)  # analysis_type
    analysis_finished = Signal(str, bool)  # analysis_type, success
    
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
        title_label = QLabel("Motion Analysis")
        title_label.setStyleSheet("""
            QLabel {
                color: rgba(226, 232, 240, 1);
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 8px;
            }
        """)
        header_card.content_layout.addWidget(title_label)
        
        # Analysis status
        self.status_label = QLabel("Ready to analyze")
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
        
        # Left panel - Analysis controls
        controls_card = GlassCard("Analysis Controls")
        controls_layout = controls_card.createVerticalLayout()
        
        # Analysis steps
        steps_group = QGroupBox("Analysis Steps")
        steps_layout = QVBoxLayout(steps_group)
        steps_layout.setContentsMargins(16, 16, 16, 16)
        
        # Step 1: Pose Estimation
        step1_layout = QHBoxLayout()
        self.pose_estimation_btn = NeuroButton("1. Pose Estimation", "primary")
        self.pose_estimation_btn.setMinimumHeight(40)
        step1_layout.addWidget(self.pose_estimation_btn)
        steps_layout.addLayout(step1_layout)
        
        # Step 2: Triangulation
        step2_layout = QHBoxLayout()
        self.triangulation_btn = NeuroButton("2. Triangulation", "primary")
        self.triangulation_btn.setMinimumHeight(40)
        step2_layout.addWidget(self.triangulation_btn)
        steps_layout.addLayout(step2_layout)
        
        # Step 3: Tracking
        step3_layout = QHBoxLayout()
        self.tracking_btn = NeuroButton("3. Tracking", "primary")
        self.tracking_btn.setMinimumHeight(40)
        step3_layout.addWidget(self.tracking_btn)
        steps_layout.addLayout(step3_layout)
        
        controls_layout.addWidget(steps_group)
        
        # Analysis options
        options_group = QGroupBox("Analysis Options")
        options_layout = QVBoxLayout(options_group)
        options_layout.setContentsMargins(16, 16, 16, 16)
        
        # Pose estimation options
        self.confidence_threshold_cb = QCheckBox("Set confidence threshold")
        self.confidence_threshold_cb.setChecked(True)
        options_layout.addWidget(self.confidence_threshold_cb)
        
        # Triangulation options
        self.optimize_reconstruction_cb = QCheckBox("Optimize 3D reconstruction")
        self.optimize_reconstruction_cb.setChecked(True)
        options_layout.addWidget(self.optimize_reconstruction_cb)
        
        # Tracking options
        self.smooth_trajectories_cb = QCheckBox("Smooth trajectories")
        self.smooth_trajectories_cb.setChecked(True)
        options_layout.addWidget(self.smooth_trajectories_cb)
        
        controls_layout.addWidget(options_group)
        
        # Control buttons
        control_buttons = QVBoxLayout()
        
        self.cancel_analysis_btn = NeuroButton("Cancel Analysis", "secondary")
        self.cancel_analysis_btn.setEnabled(False)
        control_buttons.addWidget(self.cancel_analysis_btn)
        
        controls_layout.addLayout(control_buttons)
        
        main_layout.addWidget(controls_card)
        
        # Right panel - Results
        results_card = GlassCard("Analysis Results")
        results_layout = results_card.createVerticalLayout()
        
        # Results table
        self.results_table = QTableWidget()
        self.results_table.setColumnCount(3)
        self.results_table.setHorizontalHeaderLabels(["Step", "Status", "Result"])
        self.results_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.results_table.setMaximumHeight(200)
        results_layout.addWidget(self.results_table)
        
        # Results text
        self.results_text = QTextEdit()
        self.results_text.setMaximumHeight(150)
        self.results_text.setPlaceholderText("Detailed analysis results will appear here...")
        results_layout.addWidget(self.results_text)
        
        main_layout.addWidget(results_card)
        
        layout.addLayout(main_layout)
        
    def set_viewmodel(self, viewmodel):
        """ViewModel 설정 및 이벤트 연결"""
        self.viewmodel = viewmodel
        
        # Connect signals
        self.viewmodel.analysis_started.connect(self.on_analysis_started)
        self.viewmodel.analysis_progress.connect(self.on_analysis_progress)
        self.viewmodel.analysis_finished.connect(self.on_analysis_finished)
        self.viewmodel.analysis_result.connect(self.on_analysis_result)
        self.viewmodel.error_occurred.connect(self.on_error_occurred)
        self.viewmodel.busy_changed.connect(self.on_busy_changed)
        
        # Connect button events
        self.pose_estimation_btn.clicked.connect(self.on_pose_estimation_clicked)
        self.triangulation_btn.clicked.connect(self.on_triangulation_clicked)
        self.tracking_btn.clicked.connect(self.on_tracking_clicked)
        self.cancel_analysis_btn.clicked.connect(self.on_cancel_analysis_clicked)
        
    def on_analysis_started(self, analysis_type):
        """분석 시작됨"""
        self.status_label.setText(f"{analysis_type.replace('_', ' ').title()} started...")
        self.status_label.setStyleSheet("""
            QLabel {
                color: rgba(59, 130, 246, 1);
                font-size: 16px;
                font-weight: 600;
            }
        """)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
    def on_analysis_progress(self, progress):
        """분석 진행률 업데이트"""
        self.progress_bar.setValue(progress)
        
    def on_analysis_finished(self, analysis_type, success):
        """분석 완료됨"""
        if success:
            self.status_label.setText(f"{analysis_type.replace('_', ' ').title()} completed successfully")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: rgba(34, 197, 94, 1);
                    font-size: 16px;
                    font-weight: 600;
                }
            """)
        else:
            self.status_label.setText(f"{analysis_type.replace('_', ' ').title()} failed")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: rgba(239, 68, 68, 1);
                    font-size: 16px;
                    font-weight: 600;
                }
            """)
            
        self.progress_bar.setVisible(False)
        
    def on_analysis_result(self, results):
        """분석 결과 업데이트"""
        # Update results table
        step_name = results["analysis_type"].replace("_", " ").title()
        status = "Completed" if results else "Failed"
        
        # Add or update row
        row_count = self.results_table.rowCount()
        self.results_table.setRowCount(row_count + 1)
        
        self.results_table.setItem(row_count, 0, QTableWidgetItem(step_name))
        self.results_table.setItem(row_count, 1, QTableWidgetItem(status))
        
        if results["analysis_type"] == "pose_estimation":
            result_text = f"Frames: {results['processed_frames']}, Keypoints: {results['keypoints_detected']}"
        elif results["analysis_type"] == "triangulation":
            result_text = f"Points: {results['reconstructed_points']}, Error: {results['reprojection_error']:.2f}"
        elif results["analysis_type"] == "tracking":
            result_text = f"Markers: {results['tracked_markers']}, Accuracy: {results['tracking_accuracy']:.2f}"
        else:
            result_text = "Analysis completed"
            
        self.results_table.setItem(row_count, 2, QTableWidgetItem(result_text))
        
        # Update results text
        result_text = f"""
Analysis Results:
- Type: {results['analysis_type']}
- Output: {results['output_path']}
        """.strip()
        
        self.results_text.append(result_text)
        
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
        self.pose_estimation_btn.setEnabled(not busy)
        self.triangulation_btn.setEnabled(not busy)
        self.tracking_btn.setEnabled(not busy)
        self.cancel_analysis_btn.setEnabled(busy)
        
    def on_pose_estimation_clicked(self):
        """포즈 추정 버튼 클릭"""
        asyncio.create_task(self.viewmodel.start_pose_estimation())
        
    def on_triangulation_clicked(self):
        """트라이앵귤레이션 버튼 클릭"""
        asyncio.create_task(self.viewmodel.start_triangulation())
        
    def on_tracking_clicked(self):
        """트래킹 버튼 클릭"""
        asyncio.create_task(self.viewmodel.start_tracking())
        
    def on_cancel_analysis_clicked(self):
        """분석 취소 버튼 클릭"""
        self.viewmodel.cancel_analysis()