"""System tray integration."""

import sys
from pathlib import Path

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu, QApplication
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QObject, pyqtSignal, QMetaObject, Qt


class SystemTray(QObject):
    """System tray icon with context menu."""

    show_window = pyqtSignal()
    hide_window = pyqtSignal()
    capture_now = pyqtSignal()
    toggle_auto = pyqtSignal()
    show_settings = pyqtSignal()
    show_about = pyqtSignal()
    quit_app = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._tray_icon = None
        self._auto_translate_action = None
        self._auto_translate_enabled = False

    def setup(self) -> bool:
        """
        Set up the system tray icon.
        
        Returns:
            True if successful, False if system tray not available.
        """
        if not QSystemTrayIcon.isSystemTrayAvailable():
            return False

        # Create icon
        icon = self._load_icon()
        self._tray_icon = QSystemTrayIcon(icon)

        # Create context menu
        menu = self._create_menu()
        self._tray_icon.setContextMenu(menu)

        # Connect signals
        self._tray_icon.activated.connect(self._on_activated)

        return True

    def _load_icon(self) -> QIcon:
        """Load application icon."""
        # Try to load from resources first
        icon_paths = [
            ":/icon.png",
            str(Path(__file__).parent.parent / "resources" / "icon.png"),
            str(Path(__file__).parent.parent / "resources" / "icon.svg"),
        ]

        for path in icon_paths:
            if Path(path).exists() or path.startswith(":/"):
                icon = QIcon(path)
                if not icon.isNull():
                    return icon

        # Fallback to default icon
        return QApplication.style().standardIcon(
            QApplication.style().StandardPixmap.SP_DialogOkButton
        )

    def _create_menu(self) -> QMenu:
        """Create context menu."""
        menu = QMenu()

        # Show/Hide action
        self._show_action = menu.addAction("Show Window")
        self._show_action.triggered.connect(lambda: self.show_window.emit())

        # Capture action
        capture_action = menu.addAction("Capture Now")
        capture_action.triggered.connect(lambda: self.capture_now.emit())

        # Auto-translate toggle
        self._auto_translate_action = menu.addAction("Auto-translate: Off")
        self._auto_translate_action.setCheckable(True)
        self._auto_translate_action.triggered.connect(self._on_auto_toggle)

        menu.addSeparator()

        # Settings
        settings_action = menu.addAction("Settings")
        settings_action.triggered.connect(lambda: self.show_settings.emit())

        # About
        about_action = menu.addAction("About")
        about_action.triggered.connect(lambda: self.show_about.emit())

        menu.addSeparator()

        # Quit
        quit_action = menu.addAction("Quit")
        quit_action.triggered.connect(lambda: self.quit_app.emit())

        return menu

    def _on_activated(self, reason: QSystemTrayIcon.ActivationReason) -> None:
        """Handle tray icon activation."""
        if reason == QSystemTrayIcon.ActivationReason.DoubleClick:
            self.show_window.emit()

    def _on_auto_toggle(self, checked: bool) -> None:
        """Handle auto-translate toggle."""
        self._auto_translate_enabled = checked
        self._auto_translate_action.setText(
            f"Auto-translate: {'On' if checked else 'Off'}"
        )
        self.toggle_auto.emit()

    def show(self) -> None:
        """Show the tray icon."""
        if self._tray_icon:
            self._tray_icon.show()

    def hide(self) -> None:
        """Hide the tray icon."""
        if self._tray_icon:
            self._tray_icon.hide()

    def set_auto_translate_enabled(self, enabled: bool) -> None:
        """Update auto-translate menu state."""
        if self._auto_translate_action:
            self._auto_translate_action.setChecked(enabled)
            self._auto_translate_action.setText(
                f"Auto-translate: {'On' if enabled else 'Off'}"
            )

    def show_message(self, title: str, message: str,
                     icon: QSystemTrayIcon.MessageIcon = QSystemTrayIcon.MessageIcon.Information) -> None:
        """Show a notification message."""
        if self._tray_icon and self._tray_icon.isVisible():
            self._tray_icon.showMessage(title, message, icon, 5000)
