"""
Smoke tests for Go2Rep v2.0

Basic tests to verify core functionality works.
"""

import pytest
import sys
from pathlib import Path

# Add go2rep to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent))

from utils.logger import setup_logger, get_logger
from utils.config import Config


class TestLogger:
    """Test logger functionality."""
    
    def test_logger_setup(self):
        """Test logger initialization without exceptions."""
        logger = setup_logger("test_logger")
        assert logger is not None
        assert logger.name == "test_logger"
        
    def test_get_logger(self):
        """Test get_logger function."""
        logger = get_logger("test_get_logger")
        assert logger is not None
        assert logger.name == "test_get_logger"


class TestConfig:
    """Test configuration functionality."""
    
    def test_config_initialization(self):
        """Test config initialization."""
        config = Config()
        assert config is not None
        
    def test_config_get_default(self):
        """Test config get with default value."""
        config = Config()
        value = config.get("NONEXISTENT_KEY", "default_value")
        assert value == "default_value"
        
    def test_config_set_get(self):
        """Test config set and get."""
        config = Config()
        config.set("test_key", "test_value")
        value = config.get("test_key")
        assert value == "test_value"


class TestStyles:
    """Test UI styles."""
    
    def test_qss_file_exists(self):
        """Test that QSS file exists and is not empty."""
        qss_path = Path(__file__).parent.parent / "ui" / "styles" / "glass.qss"
        assert qss_path.exists(), f"QSS file not found: {qss_path}"
        
        # Check file is not empty
        content = qss_path.read_text(encoding='utf-8')
        assert len(content) > 0, "QSS file is empty"
        assert "Glassmorphism" in content, "QSS file should contain Glassmorphism styles"


class TestProjectStructure:
    """Test project structure."""
    
    def test_main_module_exists(self):
        """Test that main module can be imported."""
        try:
            from main import main
            assert callable(main)
        except ImportError as e:
            pytest.fail(f"Failed to import main module: {e}")
            
    def test_main_window_exists(self):
        """Test that main window can be imported."""
        try:
            from ui.main_window import MainWindow
            assert MainWindow is not None
        except ImportError as e:
            pytest.fail(f"Failed to import MainWindow: {e}")


@pytest.mark.qt
class TestQtIntegration:
    """Test Qt integration (requires pytest-qt)."""
    
    def test_qapplication_creation(self, qtbot):
        """Test QApplication creation."""
        from PySide6.QtWidgets import QApplication
        
        # QApplication should already be created by pytest-qt
        app = QApplication.instance()
        assert app is not None
        
    def test_main_window_creation(self, qtbot):
        """Test MainWindow creation."""
        from ui.main_window import MainWindow
        
        window = MainWindow()
        assert window is not None
        assert window.windowTitle() == "Go2Rep v2.0 - Markerless Motion Capture"
        
        # Test window can be shown (but don't actually show it)
        qtbot.addWidget(window)
