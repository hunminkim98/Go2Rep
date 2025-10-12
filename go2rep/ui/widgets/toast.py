"""
Toast notification widget

Provides temporary status messages with auto-dismiss functionality.
"""

from PySide6.QtWidgets import QWidget, QLabel, QVBoxLayout, QHBoxLayout, QPushButton
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QFont


class Toast(QWidget):
    """
    Toast notification widget
    
    Features:
    - Auto-dismiss after specified duration
    - Slide-in animation
    - Success/Error/Warning/Info variants
    - Click to dismiss
    """
    
    def __init__(self, message: str, toast_type: str = "info", duration: int = 3000, parent=None):
        super().__init__(parent)
        self.message = message
        self.toast_type = toast_type
        self.duration = duration
        
        self.setup_ui()
        self.setup_animation()
        
        # Auto-dismiss timer
        self.dismiss_timer = QTimer()
        self.dismiss_timer.timeout.connect(self.dismiss)
        self.dismiss_timer.setSingleShot(True)
        
    def setup_ui(self):
        """Setup toast UI"""
        self.setFixedHeight(60)
        self.setMinimumWidth(300)
        self.setMaximumWidth(500)
        
        # Main layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        # Icon/Type indicator
        self.type_label = QLabel()
        self.type_label.setFixedSize(24, 24)
        self.type_label.setAlignment(Qt.AlignCenter)
        
        # Message label
        self.message_label = QLabel(self.message)
        self.message_label.setWordWrap(True)
        self.message_label.setStyleSheet("""
            QLabel {
                color: rgba(226, 232, 240, 1);
                font-size: 14px;
                font-weight: 500;
            }
        """)
        
        # Close button
        self.close_btn = QPushButton("×")
        self.close_btn.setFixedSize(24, 24)
        self.close_btn.setStyleSheet("""
            QPushButton {
                background-color: transparent;
                border: none;
                color: rgba(226, 232, 240, 0.7);
                font-size: 18px;
                font-weight: bold;
            }
            QPushButton:hover {
                color: rgba(226, 232, 240, 1);
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 12px;
            }
        """)
        self.close_btn.clicked.connect(self.dismiss)
        
        # Add to layout
        layout.addWidget(self.type_label)
        layout.addWidget(self.message_label, stretch=1)
        layout.addWidget(self.close_btn)
        
        # Apply type-specific styling
        self.apply_type_styling()
        
    def apply_type_styling(self):
        """Apply styling based on toast type"""
        base_style = """
            Toast {
                background-color: rgba(21, 21, 21, 0.95);
                border: 1px solid rgba(255, 255, 255, 0.1);
                border-radius: 8px;
            }
        """
        
        if self.toast_type == "success":
            self.type_label.setText("✓")
            self.type_label.setStyleSheet("color: rgba(34, 197, 94, 1); font-size: 16px; font-weight: bold;")
            self.setStyleSheet(base_style + """
                Toast {
                    border-left: 4px solid rgba(34, 197, 94, 1);
                }
            """)
        elif self.toast_type == "error":
            self.type_label.setText("✕")
            self.type_label.setStyleSheet("color: rgba(239, 68, 68, 1); font-size: 16px; font-weight: bold;")
            self.setStyleSheet(base_style + """
                Toast {
                    border-left: 4px solid rgba(239, 68, 68, 1);
                }
            """)
        elif self.toast_type == "warning":
            self.type_label.setText("⚠")
            self.type_label.setStyleSheet("color: rgba(245, 158, 11, 1); font-size: 16px; font-weight: bold;")
            self.setStyleSheet(base_style + """
                Toast {
                    border-left: 4px solid rgba(245, 158, 11, 1);
                }
            """)
        else:  # info
            self.type_label.setText("ℹ")
            self.type_label.setStyleSheet("color: rgba(59, 130, 246, 1); font-size: 16px; font-weight: bold;")
            self.setStyleSheet(base_style + """
                Toast {
                    border-left: 4px solid rgba(59, 130, 246, 1);
                }
            """)
            
    def setup_animation(self):
        """Setup slide-in animation"""
        self.slide_animation = QPropertyAnimation(self, b"geometry")
        self.slide_animation.setDuration(300)
        self.slide_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
    def show_toast(self):
        """Show toast with animation"""
        # Start auto-dismiss timer
        if self.duration > 0:
            self.dismiss_timer.start(self.duration)
            
        # Show with animation
        self.show()
        
    def dismiss(self):
        """Dismiss toast"""
        self.dismiss_timer.stop()
        self.hide()
        self.deleteLater()
        
    def mousePressEvent(self, event):
        """Click to dismiss"""
        if event.button() == Qt.LeftButton:
            self.dismiss()
        super().mousePressEvent(event)


class ToastManager(QWidget):
    """
    Manages multiple toast notifications
    
    Provides a container for stacking toast notifications.
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("ToastManager")
        self.toasts = []
        
        # Setup layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(8)
        self.layout.setAlignment(Qt.AlignTop | Qt.AlignRight)
        
        # Style
        self.setStyleSheet("""
            ToastManager {
                background-color: transparent;
            }
        """)
        
    def show_toast(self, message: str, toast_type: str = "info", duration: int = 3000):
        """Show a new toast notification"""
        toast = Toast(message, toast_type, duration, self)
        toast.setObjectName("Toast")
        
        # Add to layout
        self.layout.addWidget(toast)
        self.toasts.append(toast)
        
        # Connect dismiss signal
        toast.dismissed = lambda: self.remove_toast(toast)
        
        # Show toast
        toast.show_toast()
        
    def remove_toast(self, toast):
        """Remove toast from manager"""
        if toast in self.toasts:
            self.toasts.remove(toast)
            self.layout.removeWidget(toast)
            
    def clear_all(self):
        """Clear all toast notifications"""
        for toast in self.toasts[:]:
            toast.dismiss()
