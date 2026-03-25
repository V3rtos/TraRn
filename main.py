#!/usr/bin/env python3
"""TraRn - Screen Translation Application - Main entry point."""

import sys
from pathlib import Path

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from src.main_window import MainWindow
from src.settings import Settings


def main():
    """Main application entry point."""
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )

    app = QApplication(sys.argv)
    app.setApplicationName("TraRn")
    app.setApplicationVersion("0.1.0")
    app.setOrganizationName("TraRn")

    # Set application font
    font = QFont("Sans Serif", 10)
    app.setFont(font)

    # Load settings
    settings = Settings()

    # Check if should start minimized
    start_minimized = settings.get("start_minimized", False)

    # Create main window
    window = MainWindow(settings)

    # Show window (or hide if starting minimized and tray available)
    if not start_minimized:
        window.show()

    # Run application
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
