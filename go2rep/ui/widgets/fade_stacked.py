"""
Fade transition stacked widget

Provides smooth fade transitions between stacked widgets
"""

from PySide6.QtWidgets import QStackedWidget, QGraphicsOpacityEffect
from PySide6.QtCore import QPropertyAnimation, QEasingCurve, QTimer


class FadeStackedWidget(QStackedWidget):
    """
    Stacked widget with fade transitions
    
    Features:
    - Smooth fade out/in transitions
    - Configurable animation duration
    - Non-blocking transitions
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.animation_duration = 300
        self.current_effect = None
        self.next_index = None
        
    def setCurrentIndex(self, index):
        """Set current index with fade transition"""
        if index == self.currentIndex():
            return
            
        if self.count() == 0:
            super().setCurrentIndex(index)
            return
            
        self.next_index = index
        self.start_fade_transition()
        
    def start_fade_transition(self):
        """Start fade out transition"""
        current_widget = self.currentWidget()
        if not current_widget:
            super().setCurrentIndex(self.next_index)
            return
            
        # Create opacity effect for current widget
        self.current_effect = QGraphicsOpacityEffect()
        current_widget.setGraphicsEffect(self.current_effect)
        
        # Fade out animation
        fade_out = QPropertyAnimation(self.current_effect, b"opacity")
        fade_out.setDuration(self.animation_duration // 2)
        fade_out.setStartValue(1.0)
        fade_out.setEndValue(0.0)
        fade_out.setEasingCurve(QEasingCurve.Type.InOutCubic)
        
        # Connect to fade in
        fade_out.finished.connect(self.fade_in)
        fade_out.start()
        
    def fade_in(self):
        """Fade in the next widget"""
        # Switch to next widget
        super().setCurrentIndex(self.next_index)
        
        next_widget = self.currentWidget()
        if not next_widget:
            return
            
        # Create opacity effect for next widget
        next_effect = QGraphicsOpacityEffect()
        next_widget.setGraphicsEffect(next_effect)
        next_effect.setOpacity(0.0)
        
        # Fade in animation
        fade_in = QPropertyAnimation(next_effect, b"opacity")
        fade_in.setDuration(self.animation_duration // 2)
        fade_in.setStartValue(0.0)
        fade_in.setEndValue(1.0)
        fade_in.setEasingCurve(QEasingCurve.Type.InOutCubic)
        
        # Clean up after animation
        fade_in.finished.connect(self.cleanup_effects)
        fade_in.start()
        
    def cleanup_effects(self):
        """Clean up opacity effects"""
        if self.current_effect:
            self.current_effect.deleteLater()
            self.current_effect = None
            
        current_widget = self.currentWidget()
        if current_widget and current_widget.graphicsEffect():
            current_widget.graphicsEffect().deleteLater()
            current_widget.setGraphicsEffect(None)
            
    def setAnimationDuration(self, duration):
        """Set animation duration in milliseconds"""
        self.animation_duration = duration
