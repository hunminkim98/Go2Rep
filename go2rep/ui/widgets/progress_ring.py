"""
Circular progress indicator widget

Features:
- Circular progress ring
- Animated progress updates
- Customizable colors and size
"""

from PySide6.QtWidgets import QWidget, QVBoxLayout, QLabel
from PySide6.QtCore import Qt, QTimer, QPropertyAnimation, QEasingCurve
from PySide6.QtGui import QPainter, QPen, QColor, QFont


class ProgressRing(QWidget):
    """
    Circular progress indicator
    
    Features:
    - Circular progress ring
    - Animated progress updates
    - Customizable colors and size
    """
    
    def __init__(self, size=100, parent=None):
        super().__init__(parent)
        self.size = size
        self.progress = 0
        self.max_progress = 100
        self.ring_width = 8
        self.ring_color = QColor(124, 58, 237, 200)  # ACCENT
        self.background_color = QColor(31, 35, 48, 100)  # SURFACE_ALT
        self.text_color = QColor(226, 232, 240, 255)  # slate-200
        
        self.setFixedSize(size, size)
        self.setMinimumSize(size, size)
        
    def set_progress(self, value):
        """진행률 설정 (0-100)"""
        self.progress = max(0, min(100, value))
        self.update()
        
    def set_max_progress(self, value):
        """최대값 설정"""
        self.max_progress = value
        
    def set_ring_color(self, color):
        """링 색상 설정"""
        self.ring_color = color
        self.update()
        
    def set_background_color(self, color):
        """배경 색상 설정"""
        self.background_color = color
        self.update()
        
    def set_text_color(self, color):
        """텍스트 색상 설정"""
        self.text_color = color
        self.update()
        
    def paintEvent(self, event):
        """그리기 이벤트"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 중심점과 반지름 계산
        center_x = self.width() // 2
        center_y = self.height() // 2
        radius = min(center_x, center_y) - self.ring_width // 2
        
        # 배경 링 그리기
        bg_pen = QPen(self.background_color, self.ring_width)
        painter.setPen(bg_pen)
        painter.drawArc(
            center_x - radius, center_y - radius,
            radius * 2, radius * 2,
            0, 360 * 16
        )
        
        # 진행 링 그리기
        if self.progress > 0:
            progress_pen = QPen(self.ring_color, self.ring_width)
            painter.setPen(progress_pen)
            
            # 시작 각도 (12시 방향)
            start_angle = 90 * 16
            # 진행 각도
            span_angle = -int((self.progress / 100) * 360 * 16)
            
            painter.drawArc(
                center_x - radius, center_y - radius,
                radius * 2, radius * 2,
                start_angle, span_angle
            )
        
        # 텍스트 그리기
        painter.setPen(self.text_color)
        painter.setFont(QFont("Arial", 12, QFont.Bold))
        text = f"{int(self.progress)}%"
        
        # 텍스트 중앙 정렬
        text_rect = painter.fontMetrics().boundingRect(text)
        text_x = center_x - text_rect.width() // 2
        text_y = center_y + text_rect.height() // 4
        
        painter.drawText(text_x, text_y, text)
        
    def animate_progress(self, target_value, duration=1000):
        """진행률 애니메이션"""
        animation = QPropertyAnimation(self, b"progress")
        animation.setDuration(duration)
        animation.setStartValue(self.progress)
        animation.setEndValue(target_value)
        animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        animation.start()
        return animation


class LoadingSpinner(QWidget):
    """
    로딩 스피너 위젯
    
    Features:
    - 회전하는 원형 스피너
    - 자동 애니메이션
    - 시작/정지 제어
    """
    
    def __init__(self, size=40, parent=None):
        super().__init__(parent)
        self.size = size
        self.angle = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_angle)
        
        self.setFixedSize(size, size)
        self.setMinimumSize(size, size)
        
    def start_animation(self):
        """애니메이션 시작"""
        self.timer.start(50)  # 20 FPS
        
    def stop_animation(self):
        """애니메이션 정지"""
        self.timer.stop()
        
    def update_angle(self):
        """각도 업데이트"""
        self.angle = (self.angle + 10) % 360
        self.update()
        
    def paintEvent(self, event):
        """그리기 이벤트"""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        
        # 중심점과 반지름 계산
        center_x = self.width() // 2
        center_y = self.height() // 2
        radius = min(center_x, center_y) - 4
        
        # 회전하는 링 그리기
        pen = QPen(QColor(124, 58, 237, 200), 4)  # ACCENT
        painter.setPen(pen)
        
        # 회전 적용
        painter.translate(center_x, center_y)
        painter.rotate(self.angle)
        painter.translate(-center_x, -center_y)
        
        # 호 그리기 (3/4 원)
        painter.drawArc(
            center_x - radius, center_y - radius,
            radius * 2, radius * 2,
            0, 270 * 16
        )
