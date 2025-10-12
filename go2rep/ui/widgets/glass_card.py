"""
Glassmorphism + Neumorphism 스타일 카드 위젯

Features:
- 반투명 배경 (50% opacity)
- 블러 효과 (backdrop-filter 시뮬레이션)
- 소프트 그림자 (neumorphism)
- 호버 애니메이션
"""

from PySide6.QtWidgets import QFrame, QVBoxLayout, QHBoxLayout, QLabel, QWidget, QGraphicsDropShadowEffect, QLayout
from PySide6.QtCore import Qt, QPropertyAnimation, QEasingCurve, QRect
from PySide6.QtGui import QColor


class GlassCard(QFrame):
    """
    Glassmorphism + Neumorphism 스타일 카드 위젯
    
    Features:
    - 반투명 배경 (50% opacity)
    - 블러 효과 (backdrop-filter 시뮬레이션)
    - 소프트 그림자 (neumorphism)
    - 호버 애니메이션
    """
    
    def __init__(self, title=None, parent=None):
        super().__init__(parent)
        self.setObjectName("GlassCard")
        self.setup_effects()
        
        # Create root layout once
        self._root_layout = QVBoxLayout(self)
        self._root_layout.setContentsMargins(24, 24, 24, 24)
        self._root_layout.setSpacing(16)
        
        # Add title if provided
        if title:
            self._title_label = QLabel(title)
            self._title_label.setStyleSheet("""
                QLabel {
                    color: rgba(226, 232, 240, 1);
                    font-size: 16px;
                    font-weight: 600;
                    letter-spacing: 0.5px;
                    margin-bottom: 8px;
                    text-transform: uppercase;
                }
            """)
            self._root_layout.addWidget(self._title_label)
        
        # Create content widget and layout for user content
        self._content_widget = QWidget(self)
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(8)
        self._root_layout.addWidget(self._content_widget)
    
    def setup_effects(self):
        """그림자 효과 설정"""
        # Neumorphism shadow effect
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(20)
        shadow.setXOffset(4)
        shadow.setYOffset(4)
        shadow.setColor(QColor(0, 0, 0, 40))  # 40% opacity black
        self.setGraphicsEffect(shadow)
        
    def enterEvent(self, event):
        """호버 시 살짝 들어올리는 애니메이션"""
        self.animate_elevation(8)
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        """호버 해제 시 원위치"""
        self.animate_elevation(4)
        super().leaveEvent(event)
        
    def animate_elevation(self, target_y):
        """Y 오프셋 애니메이션"""
        shadow = self.graphicsEffect()
        if shadow:
            animation = QPropertyAnimation(shadow, b"yOffset")
            animation.setDuration(200)
            animation.setStartValue(shadow.yOffset())
            animation.setEndValue(target_y)
            animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            animation.start()
            # 애니메이션 객체를 저장해야 GC 방지
            self._animation = animation
    
    @property
    def content_layout(self) -> QVBoxLayout:
        return self._content_layout
    
    def addContentWidget(self, w: QWidget) -> None:
        self._content_layout.addWidget(w)
    
    def addContentLayout(self, l: QLayout) -> None:
        self._content_layout.addLayout(l)
    
    def createHorizontalLayout(self) -> QHBoxLayout:
        """수평 레이아웃 생성 헬퍼"""
        layout = QHBoxLayout()
        self._content_layout.addLayout(layout)
        return layout
    
    def createVerticalLayout(self) -> QVBoxLayout:
        """수직 레이아웃 생성 헬퍼"""
        layout = QVBoxLayout()
        self._content_layout.addLayout(layout)
        return layout


class NeuroCard(QFrame):
    """
    Neumorphism 전용 카드 위젯
    
    Features:
    - 더 강한 그림자 효과
    - 눌리는 애니메이션
    """
    
    def __init__(self, title=None, parent=None):
        super().__init__(parent)
        self.setObjectName("NeuroCard")
        self.setup_effects()
        
        # Create root layout once
        self._root_layout = QVBoxLayout(self)
        self._root_layout.setContentsMargins(24, 24, 24, 24)
        self._root_layout.setSpacing(16)
        
        # Add title if provided
        if title:
            self._title_label = QLabel(title)
            self._title_label.setStyleSheet("""
                QLabel {
                    color: rgba(226, 232, 240, 1);
                    font-size: 18px;
                    font-weight: 700;
                    letter-spacing: 0.5px;
                    margin-bottom: 12px;
                    text-transform: uppercase;
                }
            """)
            self._root_layout.addWidget(self._title_label)
        
        # Create content widget and layout for user content
        self._content_widget = QWidget(self)
        self._content_layout = QVBoxLayout(self._content_widget)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(8)
        self._root_layout.addWidget(self._content_widget)
    
    def setup_effects(self):
        """Neumorphism 그림자 효과"""
        # 더 강한 그림자 효과
        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(30)
        shadow.setXOffset(8)
        shadow.setYOffset(8)
        shadow.setColor(QColor(0, 0, 0, 60))  # 60% opacity black
        self.setGraphicsEffect(shadow)
        
    def mousePressEvent(self, event):
        """클릭 시 살짝 눌리는 효과"""
        if event.button() == Qt.LeftButton:
            self.animate_press(True)
        super().mousePressEvent(event)
        
    def mouseReleaseEvent(self, event):
        """릴리즈 시 원위치"""
        if event.button() == Qt.LeftButton:
            self.animate_press(False)
        super().mouseReleaseEvent(event)
        
    def animate_press(self, pressed):
        """눌림 애니메이션"""
        shadow = self.graphicsEffect()
        if shadow:
            target_y = 2 if pressed else 8
            animation = QPropertyAnimation(shadow, b"yOffset")
            animation.setDuration(100)
            animation.setStartValue(shadow.yOffset())
            animation.setEndValue(target_y)
            animation.setEasingCurve(QEasingCurve.Type.OutCubic)
            animation.start()
            self._press_animation = animation
    
    @property
    def content_layout(self) -> QVBoxLayout:
        return self._content_layout
    
    def addContentWidget(self, w: QWidget) -> None:
        self._content_layout.addWidget(w)
    
    def addContentLayout(self, l: QLayout) -> None:
        self._content_layout.addLayout(l)
    
    def createHorizontalLayout(self) -> QHBoxLayout:
        """수평 레이아웃 생성 헬퍼"""
        layout = QHBoxLayout()
        self._content_layout.addLayout(layout)
        return layout
    
    def createVerticalLayout(self) -> QVBoxLayout:
        """수직 레이아웃 생성 헬퍼"""
        layout = QVBoxLayout()
        self._content_layout.addLayout(layout)
        return layout
