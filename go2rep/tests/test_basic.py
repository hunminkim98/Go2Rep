"""
Basic tests for Go2Rep v2.0

Simple tests that don't require complex imports.
"""

import sys
from pathlib import Path

# Add go2rep to path for testing
sys.path.insert(0, str(Path(__file__).parent.parent))

def test_logger_setup():
    """Test logger initialization without exceptions."""
    from utils.logger import setup_logger
    
    logger = setup_logger("test_logger")
    assert logger is not None
    assert logger.name == "test_logger"
    print("✅ Logger setup test passed")

def test_config_initialization():
    """Test config initialization."""
    from utils.config import Config
    
    config = Config()
    assert config is not None
    print("✅ Config initialization test passed")

def test_config_get_default():
    """Test config get with default value."""
    from utils.config import Config
    
    config = Config()
    value = config.get("NONEXISTENT_KEY", "default_value")
    assert value == "default_value"
    print("✅ Config get default test passed")

def test_qss_file_exists():
    """Test that QSS file exists and is not empty."""
    qss_path = Path(__file__).parent.parent / "ui" / "styles" / "glass.qss"
    assert qss_path.exists(), f"QSS file not found: {qss_path}"
    
    # Check file is not empty
    content = qss_path.read_text(encoding='utf-8')
    assert len(content) > 0, "QSS file is empty"
    assert "Glassmorphism" in content, "QSS file should contain Glassmorphism styles"
    print("✅ QSS file test passed")

def test_main_module_exists():
    """Test that main module can be imported."""
    try:
        from main import main
        assert callable(main)
        print("✅ Main module import test passed")
    except ImportError as e:
        print(f"❌ Failed to import main module: {e}")
        raise

def test_main_window_exists():
    """Test that main window can be imported."""
    try:
        from ui.main_window import MainWindow
        assert MainWindow is not None
        print("✅ MainWindow import test passed")
    except ImportError as e:
        print(f"❌ Failed to import MainWindow: {e}")
        raise

if __name__ == "__main__":
    """Run tests directly."""
    print("Running Go2Rep v2.0 basic tests...")
    
    try:
        test_logger_setup()
        test_config_initialization()
        test_config_get_default()
        test_qss_file_exists()
        test_main_module_exists()
        test_main_window_exists()
        
        print("\n🎉 All basic tests passed!")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
