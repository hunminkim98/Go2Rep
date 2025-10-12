"""
PerforMetrics v2.0 - Main Entry Point

PySide6-based application with qasync integration for modern GUI.
"""

import sys
import asyncio
from pathlib import Path

from PySide6.QtWidgets import QApplication
from qasync import QEventLoop

from go2rep.ui.main_window import MainWindow
from go2rep.utils.logger import setup_logger
from go2rep.utils.config import Config
from go2rep.core.di import Container


def main():
    """Main application entry point."""
    # Setup logging
    logger = setup_logger()
    logger.info("Starting PerforMetrics v2.0")
    
    # Load configuration
    config = Config()
    logger.info(f"Configuration loaded: {config.get('APP_ENV', 'development')}")
    
    # Create Qt application
    app = QApplication(sys.argv)
    app.setApplicationName("PerforMetrics")
    app.setApplicationVersion("2.0.0-dev")
    app.setOrganizationName("PerforMetrics")
    
    # Setup asyncio event loop integration
    loop = QEventLoop(app)
    asyncio.set_event_loop(loop)
    
    # Create DI container (Mock mode by default, Mock download adapter)
    container = Container(use_mock=True, download_adapter_type="mock")
    
    # Create and show main window
    window = MainWindow(container=container)
    window.show()
    
    logger.info("Main window displayed")
    
    # Run event loop
    with loop:
        sys.exit(loop.run_forever())


if __name__ == "__main__":
    main()
