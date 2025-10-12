"""
File list management widget

Provides common file selection, management, and validation functionality.
"""

import os
from pathlib import Path
from typing import List, Optional, Callable
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, 
    QListWidget, QListWidgetItem, QLabel, QFileDialog,
    QMessageBox, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QIcon, QFont

from .neuro_button import NeuroButton


class FileListWidget(QWidget):
    """
    File list management widget
    
    Features:
    - Add/Remove files with validation
    - Drag & drop support
    - File type filtering
    - Duplicate detection
    - Select all/Clear all
    """
    
    # Signals
    files_changed = Signal(list)  # Emitted when file list changes
    file_selected = Signal(str)   # Emitted when a file is selected
    
    def __init__(self, 
                 title: str = "Files",
                 file_types: Optional[List[str]] = None,
                 allow_multiple: bool = True,
                 parent=None):
        super().__init__(parent)
        
        self.title = title
        self.file_types = file_types or ["*"]
        self.allow_multiple = allow_multiple
        self.files: List[str] = []
        
        self.setup_ui()
        
    def setup_ui(self):
        """Setup file list UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)
        
        # Header with title and buttons
        header_layout = QHBoxLayout()
        
        # Title
        title_label = QLabel(self.title)
        title_label.setStyleSheet("""
            QLabel {
                color: rgba(226, 232, 240, 1);
                font-size: 14px;
                font-weight: 600;
            }
        """)
        
        # Buttons
        self.add_btn = NeuroButton("Add Files")
        self.add_btn.clicked.connect(self.add_files)
        
        self.remove_btn = NeuroButton("Remove")
        self.remove_btn.clicked.connect(self.remove_selected)
        self.remove_btn.setEnabled(False)
        
        self.select_all_btn = NeuroButton("Select All")
        self.select_all_btn.clicked.connect(self.select_all)
        
        self.clear_btn = NeuroButton("Clear All")
        self.clear_btn.clicked.connect(self.clear_all)
        
        # Add to header
        header_layout.addWidget(title_label)
        header_layout.addStretch()
        header_layout.addWidget(self.add_btn)
        header_layout.addWidget(self.remove_btn)
        header_layout.addWidget(self.select_all_btn)
        header_layout.addWidget(self.clear_btn)
        
        # File list
        self.file_list = QListWidget()
        self.file_list.setSelectionMode(
            QAbstractItemView.ExtendedSelection if self.allow_multiple 
            else QAbstractItemView.SingleSelection
        )
        self.file_list.setStyleSheet("""
            QListWidget {
                background-color: rgba(21, 21, 21, 0.9);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
                padding: 8px;
                color: rgba(226, 232, 240, 1);
                font-size: 13px;
            }
            QListWidget::item {
                padding: 6px 8px;
                border-radius: 4px;
                margin: 1px;
            }
            QListWidget::item:selected {
                background-color: rgba(226, 232, 240, 0.15);
                color: rgba(226, 232, 240, 1);
            }
            QListWidget::item:hover {
                background-color: rgba(255, 255, 255, 0.05);
            }
        """)
        
        # Connect signals
        self.file_list.itemSelectionChanged.connect(self.on_selection_changed)
        self.file_list.itemDoubleClicked.connect(self.on_item_double_clicked)
        
        # Add to layout
        layout.addLayout(header_layout)
        layout.addWidget(self.file_list)
        
        # Enable drag & drop
        self.file_list.setDragDropMode(QAbstractItemView.DropOnly)
        self.file_list.setAcceptDrops(True)
        
    def add_files(self):
        """Add files via file dialog"""
        file_filter = ";;".join([f"{ext} files (*{ext})" for ext in self.file_types])
        
        if self.allow_multiple:
            files, _ = QFileDialog.getOpenFileNames(
                self, "Select Files", "", file_filter
            )
        else:
            file, _ = QFileDialog.getOpenFile(
                self, "Select File", "", file_filter
            )
            files = [file] if file else []
            
        if files:
            self.add_files_to_list(files)
            
    def add_files_to_list(self, files: List[str]):
        """Add files to the list with validation"""
        added_count = 0
        
        for file_path in files:
            if self.validate_file(file_path):
                if file_path not in self.files:
                    self.files.append(file_path)
                    self.add_file_item(file_path)
                    added_count += 1
                    
        if added_count > 0:
            self.files_changed.emit(self.files)
            
    def validate_file(self, file_path: str) -> bool:
        """Validate file before adding"""
        if not os.path.exists(file_path):
            return False
            
        # Check file extension
        file_ext = Path(file_path).suffix.lower()
        if self.file_types != ["*"] and file_ext not in self.file_types:
            return False
            
        return True
        
    def add_file_item(self, file_path: str):
        """Add file item to list widget"""
        item = QListWidgetItem()
        item.setText(os.path.basename(file_path))
        item.setToolTip(file_path)
        item.setData(Qt.UserRole, file_path)
        
        # Set icon based on file type
        ext = Path(file_path).suffix.lower()
        if ext in ['.mp4', '.avi', '.mov', '.mkv']:
            item.setText(f"🎥 {os.path.basename(file_path)}")
        elif ext in ['.jpg', '.jpeg', '.png', '.bmp']:
            item.setText(f"🖼 {os.path.basename(file_path)}")
        elif ext in ['.c3d', '.trc']:
            item.setText(f"📊 {os.path.basename(file_path)}")
        else:
            item.setText(f"📄 {os.path.basename(file_path)}")
            
        self.file_list.addItem(item)
        
    def remove_selected(self):
        """Remove selected files"""
        selected_items = self.file_list.selectedItems()
        if not selected_items:
            return
            
        for item in selected_items:
            file_path = item.data(Qt.UserRole)
            if file_path in self.files:
                self.files.remove(file_path)
            self.file_list.takeItem(self.file_list.row(item))
            
        self.files_changed.emit(self.files)
        
    def select_all(self):
        """Select all files"""
        self.file_list.selectAll()
        
    def clear_all(self):
        """Clear all files"""
        self.files.clear()
        self.file_list.clear()
        self.files_changed.emit(self.files)
        
    def on_selection_changed(self):
        """Handle selection change"""
        has_selection = len(self.file_list.selectedItems()) > 0
        self.remove_btn.setEnabled(has_selection)
        
    def on_item_double_clicked(self, item: QListWidgetItem):
        """Handle item double click"""
        file_path = item.data(Qt.UserRole)
        self.file_selected.emit(file_path)
        
    def get_files(self) -> List[str]:
        """Get current file list"""
        return self.files.copy()
        
    def set_files(self, files: List[str]):
        """Set file list"""
        self.clear_all()
        if files:
            self.add_files_to_list(files)
            
    def get_selected_files(self) -> List[str]:
        """Get selected files"""
        selected_files = []
        for item in self.file_list.selectedItems():
            file_path = item.data(Qt.UserRole)
            selected_files.append(file_path)
        return selected_files
        
    def update_files(self, files_data):
        """Update files from ViewModel data"""
        self.clear_all()
        for file_data in files_data:
            if isinstance(file_data, dict):
                file_path = file_data.get("path", "")
            else:
                file_path = str(file_data)
            if file_path:
                self.add_files_to_list([file_path])
                
    @property
    def itemSelectionChanged(self):
        """Expose QListWidget's itemSelectionChanged signal"""
        return self.file_list.itemSelectionChanged
        
    def dragEnterEvent(self, event):
        """Handle drag enter event"""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
        else:
            event.ignore()
            
    def dropEvent(self, event):
        """Handle drop event"""
        if event.mimeData().hasUrls():
            files = []
            for url in event.mimeData().urls():
                file_path = url.toLocalFile()
                if os.path.isfile(file_path):
                    files.append(file_path)
                    
            if files:
                self.add_files_to_list(files)
                
            event.acceptProposedAction()
        else:
            event.ignore()
