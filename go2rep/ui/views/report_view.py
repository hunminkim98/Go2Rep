"""
Report view

Provides summary and custom report generation controls
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
from ..viewmodels.report_vm import ReportViewModel


class ReportView(QWidget):
    """리포트 생성 화면"""
    
    # Signals
    report_generation_started = Signal(str)  # report_type
    report_generation_finished = Signal(str, bool)  # report_type, success
    
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
        title_label = QLabel("Report Generation")
        title_label.setStyleSheet("""
            QLabel {
                color: rgba(226, 232, 240, 1);
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 8px;
            }
        """)
        header_card.content_layout.addWidget(title_label)
        
        # Report status
        self.status_label = QLabel("Ready to generate reports")
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
        
        # Left panel - Data sources
        sources_card = GlassCard("Data Sources")
        sources_layout = sources_card.createVerticalLayout()
        
        # Data sources table
        self.sources_table = QTableWidget()
        self.sources_table.setColumnCount(4)
        self.sources_table.setHorizontalHeaderLabels(["Source", "Type", "Size", "Status"])
        self.sources_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        self.sources_table.setMaximumHeight(200)
        self.sources_table.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        sources_layout.addWidget(self.sources_table)
        
        # Data source management buttons
        source_buttons = QHBoxLayout()
        
        self.refresh_sources_btn = NeuroButton("Refresh", "primary")
        self.select_all_btn = NeuroButton("Select All", "secondary")
        self.deselect_all_btn = NeuroButton("Deselect All", "secondary")
        
        source_buttons.addWidget(self.refresh_sources_btn)
        source_buttons.addWidget(self.select_all_btn)
        source_buttons.addWidget(self.deselect_all_btn)
        
        sources_layout.addLayout(source_buttons)
        
        main_layout.addWidget(sources_card)
        
        # Right panel - Report controls
        controls_card = GlassCard("Report Controls")
        controls_layout = controls_card.createVerticalLayout()
        
        # Report types
        report_group = QGroupBox("Report Types")
        report_layout = QVBoxLayout(report_group)
        report_layout.setContentsMargins(16, 16, 16, 16)
        
        # Summary report
        summary_layout = QHBoxLayout()
        self.summary_report_btn = NeuroButton("Generate Summary Report", "primary")
        self.summary_report_btn.setMinimumHeight(40)
        summary_layout.addWidget(self.summary_report_btn)
        report_layout.addLayout(summary_layout)
        
        # Custom report
        custom_layout = QHBoxLayout()
        self.custom_report_btn = NeuroButton("Generate Custom Report", "success")
        self.custom_report_btn.setMinimumHeight(40)
        custom_layout.addWidget(self.custom_report_btn)
        report_layout.addLayout(custom_layout)
        
        controls_layout.addWidget(report_group)
        
        # Custom report options
        custom_options_group = QGroupBox("Custom Report Options")
        custom_options_layout = QVBoxLayout(custom_options_group)
        custom_options_layout.setContentsMargins(16, 16, 16, 16)
        
        # Report sections
        sections_layout = QVBoxLayout()
        sections_layout.addWidget(QLabel("Select Report Sections:"))
        
        self.executive_summary_cb = QCheckBox("Executive Summary")
        self.executive_summary_cb.setChecked(True)
        sections_layout.addWidget(self.executive_summary_cb)
        
        self.data_quality_cb = QCheckBox("Data Quality Assessment")
        self.data_quality_cb.setChecked(True)
        sections_layout.addWidget(self.data_quality_cb)
        
        self.performance_metrics_cb = QCheckBox("Key Performance Metrics")
        self.performance_metrics_cb.setChecked(True)
        sections_layout.addWidget(self.performance_metrics_cb)
        
        self.recommendations_cb = QCheckBox("Recommendations")
        self.recommendations_cb.setChecked(True)
        sections_layout.addWidget(self.recommendations_cb)
        
        self.technical_details_cb = QCheckBox("Technical Details")
        sections_layout.addWidget(self.technical_details_cb)
        
        self.appendices_cb = QCheckBox("Appendices")
        sections_layout.addWidget(self.appendices_cb)
        
        custom_options_layout.addLayout(sections_layout)
        
        controls_layout.addWidget(custom_options_group)
        
        # Control buttons
        control_buttons = QVBoxLayout()
        
        self.cancel_report_btn = NeuroButton("Cancel Report", "secondary")
        self.cancel_report_btn.setEnabled(False)
        control_buttons.addWidget(self.cancel_report_btn)
        
        controls_layout.addLayout(control_buttons)
        
        main_layout.addWidget(controls_card)
        
        layout.addLayout(main_layout)
        
        # Results panel
        results_card = GlassCard("Report Generation Results")
        results_layout = results_card.createVerticalLayout()
        
        # Results text
        self.results_text = QTextEdit()
        self.results_text.setMaximumHeight(200)
        self.results_text.setPlaceholderText("Report generation results will appear here...")
        results_layout.addWidget(self.results_text)
        
        layout.addWidget(results_card)
        
    def set_viewmodel(self, viewmodel):
        """ViewModel 설정 및 이벤트 연결"""
        self.viewmodel = viewmodel
        
        # Connect signals
        self.viewmodel.data_sources_changed.connect(self.on_data_sources_changed)
        self.viewmodel.report_generation_started.connect(self.on_report_generation_started)
        self.viewmodel.report_generation_progress.connect(self.on_report_generation_progress)
        self.viewmodel.report_generation_finished.connect(self.on_report_generation_finished)
        self.viewmodel.report_generation_result.connect(self.on_report_generation_result)
        self.viewmodel.error_occurred.connect(self.on_error_occurred)
        self.viewmodel.busy_changed.connect(self.on_busy_changed)
        
        # Connect button events
        self.refresh_sources_btn.clicked.connect(self.on_refresh_sources_clicked)
        self.select_all_btn.clicked.connect(self.on_select_all_clicked)
        self.deselect_all_btn.clicked.connect(self.on_deselect_all_clicked)
        self.summary_report_btn.clicked.connect(self.on_summary_report_clicked)
        self.custom_report_btn.clicked.connect(self.on_custom_report_clicked)
        self.cancel_report_btn.clicked.connect(self.on_cancel_report_clicked)
        
        # Connect table selection
        self.sources_table.itemSelectionChanged.connect(self.on_source_selected)
        
        # Initialize data sources
        self.viewmodel.refresh_data_sources()
        
    def on_data_sources_changed(self, sources):
        """데이터 소스 목록 변경됨"""
        self.sources_table.setRowCount(len(sources))
        
        for i, source in enumerate(sources):
            # Source name
            self.sources_table.setItem(i, 0, QTableWidgetItem(source["name"]))
            
            # Type
            self.sources_table.setItem(i, 1, QTableWidgetItem(source["type"]))
            
            # Size
            self.sources_table.setItem(i, 2, QTableWidgetItem(source["size"]))
            
            # Status
            status_item = QTableWidgetItem(source["status"])
            if source["status"] == "available":
                status_item.setForeground(Qt.GlobalColor.green)
            else:
                status_item.setForeground(Qt.GlobalColor.red)
            self.sources_table.setItem(i, 3, status_item)
            
            # Set selection state
            if source["selected"]:
                self.sources_table.selectRow(i)
                
    def on_source_selected(self):
        """데이터 소스 선택됨"""
        # Toggle selection state in viewmodel
        current_row = self.sources_table.currentRow()
        if current_row >= 0:
            sources = self.viewmodel.get_data_sources()
            if current_row < len(sources):
                source_name = sources[current_row]["name"]
                self.viewmodel.toggle_data_source(source_name)
                
    def on_report_generation_started(self, report_type):
        """리포트 생성 시작됨"""
        self.status_label.setText(f"{report_type.title()} report generation started...")
        self.status_label.setStyleSheet("""
            QLabel {
                color: rgba(59, 130, 246, 1);
                font-size: 16px;
                font-weight: 600;
            }
        """)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
    def on_report_generation_progress(self, progress):
        """리포트 생성 진행률 업데이트"""
        self.progress_bar.setValue(progress)
        
    def on_report_generation_finished(self, report_type, success):
        """리포트 생성 완료됨"""
        if success:
            self.status_label.setText(f"{report_type.title()} report generated successfully")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: rgba(34, 197, 94, 1);
                    font-size: 16px;
                    font-weight: 600;
                }
            """)
        else:
            self.status_label.setText(f"{report_type.title()} report generation failed")
            self.status_label.setStyleSheet("""
                QLabel {
                    color: rgba(239, 68, 68, 1);
                    font-size: 16px;
                    font-weight: 600;
                }
            """)
            
        self.progress_bar.setVisible(False)
        
    def on_report_generation_result(self, results):
        """리포트 생성 결과 업데이트"""
        # Update results text
        result_text = f"""
Report Generation Results:
- Type: {results['report_type']}
- Total Sources: {results['total_sources']}
- Selected Sources: {results['selected_sources']}
- Output: {results['output_path']}
        """.strip()
        
        if results['report_type'] == 'custom':
            result_text += f"\n- Custom Sections: {', '.join(results['custom_sections'])}"
            
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
        self.refresh_sources_btn.setEnabled(not busy)
        self.select_all_btn.setEnabled(not busy)
        self.deselect_all_btn.setEnabled(not busy)
        self.summary_report_btn.setEnabled(not busy)
        self.custom_report_btn.setEnabled(not busy)
        self.cancel_report_btn.setEnabled(busy)
        
    def on_refresh_sources_clicked(self):
        """데이터 소스 새로고침 버튼 클릭"""
        self.viewmodel.refresh_data_sources()
        
    def on_select_all_clicked(self):
        """모든 데이터 소스 선택 버튼 클릭"""
        self.viewmodel.select_all_data_sources()
        
    def on_deselect_all_clicked(self):
        """모든 데이터 소스 해제 버튼 클릭"""
        self.viewmodel.deselect_all_data_sources()
        
    def on_summary_report_clicked(self):
        """요약 리포트 생성 버튼 클릭"""
        asyncio.create_task(self.viewmodel.start_summary_report())
        
    def on_custom_report_clicked(self):
        """커스텀 리포트 생성 버튼 클릭"""
        # Get selected sections
        sections = []
        if self.executive_summary_cb.isChecked():
            sections.append("Executive Summary")
        if self.data_quality_cb.isChecked():
            sections.append("Data Quality Assessment")
        if self.performance_metrics_cb.isChecked():
            sections.append("Key Performance Metrics")
        if self.recommendations_cb.isChecked():
            sections.append("Recommendations")
        if self.technical_details_cb.isChecked():
            sections.append("Technical Details")
        if self.appendices_cb.isChecked():
            sections.append("Appendices")
            
        if sections:
            asyncio.create_task(self.viewmodel.start_custom_report(sections))
        else:
            self.status_label.setText("Please select at least one report section")
            
    def on_cancel_report_clicked(self):
        """리포트 생성 취소 버튼 클릭"""
        self.viewmodel.cancel_report_generation()