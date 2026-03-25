"""Area selector widget for selecting screen region."""

from PyQt6.QtWidgets import QWidget, QRubberBand, QApplication
from PyQt6.QtCore import Qt, QRect, QPoint, QSize
from PyQt6.QtGui import QCursor


class AreaSelector(QWidget):
    """Full-screen overlay for selecting a screen region."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._selected_rect = QRect()
        self._origin = QPoint()
        self._rubber_band = None
        self._selecting = False

        self._setup_ui()

    def _setup_ui(self):
        """Configure the selector widget."""
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setCursor(QCursor(Qt.CursorShape.CrossCursor))

        screen = QApplication.primaryScreen()
        if screen:
            self.setGeometry(screen.geometry())

        self._rubber_band = QRubberBand(QRubberBand.Shape.Rectangle, self)

    def showEvent(self, event):
        """Handle show event."""
        super().showEvent(event)
        self.activateWindow()
        self.setFocus()

    def mousePressEvent(self, event):
        """Start selection on mouse press."""
        if event.button() == Qt.MouseButton.LeftButton:
            self._origin = event.position().toPoint()
            self._selecting = True
            self._rubber_band.setGeometry(QRect(self._origin, QSize()))
            self._rubber_band.show()

    def mouseMoveEvent(self, event):
        """Update selection rectangle on mouse move."""
        if self._selecting:
            current = event.position().toPoint()
            rect = QRect(self._origin, current).normalized()
            self._rubber_band.setGeometry(rect)

    def mouseReleaseEvent(self, event):
        """Finish selection on mouse release."""
        if event.button() == Qt.MouseButton.LeftButton and self._selecting:
            self._selecting = False
            self._selected_rect = self._rubber_band.geometry()
            self._rubber_band.hide()

            # Only accept if rect has area
            if self._selected_rect.width() > 0 and self._selected_rect.height() > 0:
                self.hide()
                self.area_selected.emit(self._selected_rect)

    def keyPressEvent(self, event):
        """Handle key presses."""
        if event.key() == Qt.Key.Key_Escape:
            self._selecting = False
            self._rubber_band.hide()
            self.hide()
            self.selection_cancelled.emit()

    def get_selected_rect(self) -> QRect:
        """Get the selected rectangle in global coordinates."""
        if self._selected_rect.isValid():
            # Convert from widget coordinates to global
            top_left = self.mapToGlobal(self._selected_rect.topLeft())
            return QRect(top_left, self._selected_rect.size())
        return QRect()

    # Signals would be defined here in a full implementation
    # Using dynamic signals for simplicity
    area_selected = None  # type: ignore
    selection_cancelled = None  # type: ignore


# Fix: Define signals properly
from PyQt6.QtCore import pyqtSignal, QRect as QRectType


class AreaSelectorWithSignals(AreaSelector):
    """Area selector with proper Qt signals."""

    area_selected = pyqtSignal(QRectType)
    selection_cancelled = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        # Override the class-level signals with instance-level
        pass
