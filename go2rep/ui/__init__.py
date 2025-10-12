"""
UI module for Go2Rep v2.0

Contains all user interface components including:
- Main window and navigation
- Views for different workflows
- Custom widgets (Glassmorphism + Neumorphism)
- ViewModels for MVVM pattern
- Styles and themes
"""

from .main_window import MainWindow
from .widgets.glass_card import GlassCard, NeuroCard
from .widgets.neuro_button import NeuroButton, GlassButton
from .widgets.progress_ring import ProgressRing, LoadingSpinner
from .viewmodels.camera_vm import CameraViewModel

__all__ = [
    'MainWindow',
    'GlassCard',
    'NeuroCard', 
    'NeuroButton',
    'GlassButton',
    'ProgressRing',
    'LoadingSpinner',
    'CameraViewModel'
]