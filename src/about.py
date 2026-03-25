"""About dialog for the application."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QPushButton,
    QDialogButtonBox, QTextEdit, QWidget
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from . import __version__, __author__, __license__


class AboutDialog(QDialog):
    """About application dialog."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("About TraRn")
        self.setFixedSize(400, 350)
        self.setWindowModality(Qt.WindowModality.WindowModal)

        self._setup_ui()

    def _setup_ui(self):
        """Set up the dialog UI."""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Title
        title = QLabel("TraRn")
        title.setFont(QFont("Sans Serif", 18, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Version
        version_label = QLabel(f"Version {__version__}")
        version_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version_label)

        # Description
        description = QLabel(
            "Screen Translation Application\n"
            "Capture screen regions and translate text instantly."
        )
        description.setAlignment(Qt.AlignmentFlag.AlignCenter)
        description.setWordWrap(True)
        layout.addWidget(description)

        # Info text
        info_text = QTextEdit()
        info_text.setReadOnly(True)
        info_text.setMaximumHeight(120)
        info_text.setHtml(self._get_info_html())
        layout.addWidget(info_text)

        # Dependencies
        deps_label = QLabel("<b>Dependencies:</b> PyQt6, pytesseract/easyocr, deep-translator")
        deps_label.setWordWrap(True)
        layout.addWidget(deps_label)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        button_box.accepted.connect(self.accept)
        layout.addWidget(button_box)

        self.setLayout(layout)

    def _get_info_html(self) -> str:
        """Get info HTML content."""
        return f"""
        <table style="width: 100%;">
            <tr><td><b>Author:</b></td><td>{__author__}</td></tr>
            <tr><td><b>License:</b></td><td>{__license__}</td></tr>
            <tr><td><b>Platform:</b></td><td>Linux (Wayland + X11)</td></tr>
        </table>
        """
