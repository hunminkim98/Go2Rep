"""
Enhanced Neumorphic 스타일 버튼 위젯

Features:
- 클릭 시 눌리는 애니메이션
- 호버 시 스케일 효과
- Ripple effect (optional)
- 부드러운 색상 전환
"""

from PySide6.QtWidgets import QPushButton, QWidget
from PySide6.QtCore import QPropertyAnimation, QRect, QEasingCurve, Qt, QTimer, Property
from PySide6.QtGui import QColor, QPainter, QPen


class RippleWidget(QWidget):
    """Ripple effect overlay widget"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._ripple_radius = 0
        self._ripple_opacity = 0
        self.ripple_center = None
        self.animation = None
        
    def getRippleRadius(self):
        return self._ripple_radius
        
    def setRippleRadius(self, value):
        self._ripple_radius = value
        self.update()
        
    def getRippleOpacity(self):
        return self._ripple_opacity
        
    def setRippleOpacity(self, value):
        self._ripple_opacity = value
        self.update()
        
    ripple_radius = Property(float, getRippleRadius, setRippleRadius)
    ripple_opacity = Property(float, getRippleOpacity, setRippleOpacity)
        
    def start_ripple(self, center):
        """Start ripple animation from center point"""
        self.ripple_center = center
        self.ripple_radius = 0
        self.ripple_opacity = 0.6
        
        # Animate radius
        self.radius_animation = QPropertyAnimation(self, b"ripple_radius")
        self.radius_animation.setDuration(400)
        self.radius_animation.setStartValue(0)
        self.radius_animation.setEndValue(50)
        self.radius_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Animate opacity
        self.opacity_animation = QPropertyAnimation(self, b"ripple_opacity")
        self.opacity_animation.setDuration(400)
        self.opacity_animation.setStartValue(0.6)
        self.opacity_animation.setEndValue(0)
        self.opacity_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
        # Start animations
        self.radius_animation.start()
        self.opacity_animation.start()
        
        # Hide after animation
        QTimer.singleShot(400, self.hide)
        
    def paintEvent(self, event):
        """Paint ripple effect"""
        if self.ripple_center and self.ripple_radius > 0:
            painter = QPainter(self)
            painter.setRenderHint(QPainter.RenderHint.Antialiasing)
            
            # Semi-transparent white circle
            color = QColor(255, 255, 255, int(255 * self.ripple_opacity))
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)
            
            painter.drawEllipse(
                self.ripple_center.x() - self.ripple_radius,
                self.ripple_center.y() - self.ripple_radius,
                self.ripple_radius * 2,
                self.ripple_radius * 2
            )


class NeuroButton(QPushButton):
    """
    Enhanced Neumorphic 스타일 버튼
    
    Features:
    - 클릭 시 눌리는 애니메이션
    - 호버 시 스케일 효과
    - Ripple effect (optional)
    - 부드러운 색상 전환
    """
    
    def __init__(self, text, style="primary", parent=None, enable_ripple=True):
        super().__init__(text, parent)
        self.style_type = style
        self.setProperty("class", style)
        self._is_pressed = False
        self._is_hovered = False
        self.enable_ripple = enable_ripple
        
        # Ripple effect widget
        if self.enable_ripple:
            self.ripple_widget = RippleWidget(self)
            self.ripple_widget.hide()
        
        # Hover animation
        self.hover_animation = QPropertyAnimation(self, b"geometry")
        self.hover_animation.setDuration(200)
        self.hover_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        
    def enterEvent(self, event):
        """호버 시 스케일 효과"""
        self._is_hovered = True
        self.animate_hover(1.02)
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """호버 해제 시 원위치"""
        self._is_hovered = False
        self.animate_hover(1.0)
        super().leaveEvent(event)
        
    def animate_hover(self, scale):
        """호버 스케일 애니메이션"""
        current = self.geometry()
        center_x = current.x() + current.width() // 2
        center_y = current.y() + current.height() // 2
        
        new_width = int(current.width() * scale)
        new_height = int(current.height() * scale)
        
        target = QRect(
            center_x - new_width // 2,
            center_y - new_height // 2,
            new_width,
            new_height
        )
        
        self.hover_animation.stop()
        self.hover_animation.setStartValue(current)
        self.hover_animation.setEndValue(target)
        self.hover_animation.start()
        
    def mousePressEvent(self, event):
        """클릭 시 살짝 눌리는 효과 + Ripple"""
        if event.button() == Qt.LeftButton:
            self._is_pressed = True
            
            # Ripple effect
            if self.enable_ripple and hasattr(self, 'ripple_widget'):
                self.ripple_widget.resize(self.size())
                self.ripple_widget.show()
                self.ripple_widget.start_ripple(event.pos())
            
            # Geometry 애니메이션으로 버튼 크기 살짝 축소
            original = self.geometry()
            pressed = QRect(
                original.x() + 2,
                original.y() + 2,
                original.width() - 4,
                original.height() - 4
            )
            
            self.animation = QPropertyAnimation(self, b"geometry")
            self.animation.setDuration(100)
            self.animation.setStartValue(original)
            self.animation.setEndValue(pressed)
            self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            self.animation.start()
            
        super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        """릴리즈 시 원위치"""
        if event.button() == Qt.LeftButton and self._is_pressed:
            self._is_pressed = False
            # 원래 크기로 복구
            pressed = self.geometry()
            original = QRect(
                pressed.x() - 2,
                pressed.y() - 2,
                pressed.width() + 4,
                pressed.height() + 4
            )
            
            self.animation = QPropertyAnimation(self, b"geometry")
            self.animation.setDuration(150)
            self.animation.setStartValue(pressed)
            self.animation.setEndValue(original)
            self.animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            self.animation.start()
            
        super().mouseReleaseEvent(event)


class GlassButton(QPushButton):
    """
    Glassmorphism 스타일 버튼
    
    Features:
    - 반투명 배경
    - 호버 시 블러 효과 증가
    - 부드러운 전환
    """
    
    def __init__(self, text, style="primary", parent=None):
        super().__init__(text, parent)
        self.style_type = style
        self.setProperty("class", style)
        self._base_style = None
        
    def enterEvent(self, event):
        """호버 시 스타일 변경"""
        if self._base_style is None:
            self._base_style = self.styleSheet()
        
        hover_style = self._base_style.replace(
            "background-color: rgba(59, 130, 246, 0.8)",
            "background-color: rgba(96, 165, 250, 0.9)"
        ).replace(
            "background-color: rgba(30, 41, 59, 0.6)",
            "background-color: rgba(51, 65, 85, 0.7)"
        )
        
        self.setStyleSheet(hover_style)
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """호버 해제 시 원래 스타일"""
        if self._base_style:
            self.setStyleSheet(self._base_style)
        super().leaveEvent(event)
