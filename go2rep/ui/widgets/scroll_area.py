"""
Smooth scroll area widget

Provides smooth scrolling with mouse wheel support and custom scrollbar styling.
"""

from PySide6.QtWidgets import QScrollArea
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QWheelEvent


class SmoothScrollArea(QScrollArea):
    """
    Smooth scrolling area with enhanced wheel event handling
    
    Features:
    - Smooth wheel scrolling with animation
    - Custom scrollbar styling support
    - Overshoot prevention
    - Trackpad gesture support
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_scroll_area()
        
    def setup_scroll_area(self):
        """Setup scroll area properties"""
        # Enable widget resizing
        self.setWidgetResizable(True)
        
        # Scrollbar policies
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        # Scroll step size
        self.verticalScrollBar().setSingleStep(24)
        
        # Focus policy for wheel events - allow wheel events without focus
        self.setFocusPolicy(Qt.WheelFocus)
        
        # Border styling
        self.setFrameShape(QScrollArea.Shape.NoFrame)
        
        # Ensure wheel events are processed
        self.setAttribute(Qt.WA_AcceptTouchEvents, True)
        
    def wheelEvent(self, event: QWheelEvent):
        """Enhanced wheel event with smooth scrolling"""
        # Check if scrolling is needed
        scroll_bar = self.verticalScrollBar()
        if not scroll_bar.isVisible():
            # No scrollbar visible, pass event to parent
            super().wheelEvent(event)
            return
            
        # Calculate scroll delta
        delta = event.angleDelta().y()
        if delta == 0:
            # No delta, pass to parent
            super().wheelEvent(event)
            return
            
        # Calculate target scroll position
        current_value = scroll_bar.value()
        target_value = current_value - delta
        
        # Clamp to valid range
        target_value = max(scroll_bar.minimum(), 
                          min(scroll_bar.maximum(), target_value))
        
        # Direct scroll (no animation for better responsiveness)
        scroll_bar.setValue(target_value)
        
        # Accept event to prevent further propagation
        event.accept()
        
    def animate_scroll(self, start_value, end_value):
        """Animate scroll to target value"""
        if start_value == end_value:
            return
            
        # Create animation
        animation = QPropertyAnimation(self.verticalScrollBar(), b"value")
        animation.setDuration(150)  # 150ms animation
        animation.setStartValue(start_value)
        animation.setEndValue(end_value)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Start animation
        animation.start()
        
    def scroll_to_top(self):
        """Scroll to top of content"""
        self.verticalScrollBar().setValue(0)
        
    def scroll_to_bottom(self):
        """Scroll to bottom of content"""
        scroll_bar = self.verticalScrollBar()
        scroll_bar.setValue(scroll_bar.maximum())
        
    def scroll_to_widget(self, widget):
        """Scroll to make widget visible"""
        if widget and self.widget():
            # Ensure widget is visible
            self.ensureWidgetVisible(widget, 0, 0)
