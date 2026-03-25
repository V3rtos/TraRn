"""Main window with settings and translation display."""

from PyQt6.QtWidgets import (
    QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QTextEdit, QPushButton, QLabel, QComboBox,
    QSpinBox, QGroupBox, QFormLayout, QCheckBox,
    QTabWidget, QDialog, QDialogButtonBox
)
from PyQt6.QtCore import Qt, QTimer, QRect
from PyQt6.QtGui import QFont, QCloseEvent, QKeySequence, QShortcut

from .area_selector import AreaSelectorWithSignals as AreaSelector
from .screenshot import ScreenshotCapture
from .ocr import OCREngine
from .translator import Translator
from .settings import Settings
from .tray import SystemTray
from .about import AboutDialog


class SettingsDialog(QDialog):
    """Settings dialog."""

    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self._settings = settings
        self.setWindowTitle("Settings")
        self.setFixedSize(450, 400)
        self.setWindowModality(Qt.WindowModality.WindowModal)
        self._setup_ui()
        self._load_settings()

    def _setup_ui(self):
        """Set up UI."""
        layout = QVBoxLayout()
        tabs = QTabWidget()

        # Translation tab
        trans_tab = self._create_translation_tab()
        tabs.addTab(trans_tab, "Translation")

        # General tab
        general_tab = self._create_general_tab()
        tabs.addTab(general_tab, "General")

        layout.addWidget(tabs)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Save |
            QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._save_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

        self.setLayout(layout)

    def _create_translation_tab(self) -> QWidget:
        """Create translation settings tab."""
        widget = QWidget()
        layout = QFormLayout()
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        # Source language
        self._source_lang = QComboBox()
        self._source_lang.addItem("Auto-detect", "auto")
        for name, code in Translator.LANGUAGES.items():
            self._source_lang.addItem(name, code)
        layout.addRow("Source Language:", self._source_lang)

        # Target language
        self._target_lang = QComboBox()
        for name, code in Translator.LANGUAGES.items():
            self._target_lang.addItem(name, code)
        self._target_lang.setCurrentText("English")
        layout.addRow("Target Language:", self._target_lang)

        # Translation service
        self._service = QComboBox()
        self._service.addItem("Google Translate", "google")
        self._service.addItem("DeepL", "deepl")
        layout.addRow("Service:", self._service)

        # OCR engine
        self._ocr_engine = QComboBox()
        self._ocr_engine.addItem("Tesseract", "tesseract")
        self._ocr_engine.addItem("EasyOCR", "easyocr")
        # PaddleOCR is optional - only available if installed
        try:
            import paddleocr
            self._ocr_engine.addItem("PaddleOCR", "paddleocr")
        except ImportError:
            pass
        layout.addRow("OCR Engine:", self._ocr_engine)
        self._ocr_engine.currentIndexChanged.connect(self._on_engine_changed)

        # PSM mode (Tesseract only)
        self._psm_mode = QComboBox()
        for key, (name, desc) in OCREngine.PSM_MODES.items():
            self._psm_mode.addItem(f"{name} ({desc})", key)
        self._psm_mode.setToolTip("Tesseract Page Segmentation Mode")
        layout.addRow("Tesseract PSM Mode:", self._psm_mode)

        # Merge lines option
        self._merge_lines = QCheckBox("Merge lines for better translation")
        self._merge_lines.setToolTip("Combines lines into paragraphs for improved translation")
        layout.addRow(self._merge_lines)

        # GPU acceleration option
        self._use_gpu = QCheckBox("Use GPU acceleration (EasyOCR/PaddleOCR)")
        self._use_gpu.setToolTip("Enable GPU acceleration for OCR engines that support it")
        
        # GPU status label
        self._gpu_status = QLabel("")
        self._gpu_status.setStyleSheet("color: gray; font-size: 10px;")
        self._update_gpu_status()
        
        layout.addRow(self._use_gpu)
        layout.addRow("", self._gpu_status)

        widget.setLayout(layout)
        return widget

    def _on_engine_changed(self, index: int):
        """Enable/disable PSM mode based on selected engine."""
        engine = self._ocr_engine.currentData()
        self._psm_mode.setEnabled(engine == "tesseract")

    def _update_gpu_status(self):
        """Update GPU status label."""
        gpu_available, gpu_name = OCREngine.detect_gpu()
        if gpu_available:
            self._gpu_status.setText(f"✓ GPU available: {gpu_name}")
            self._gpu_status.setStyleSheet("color: green; font-size: 10px;")
            self._use_gpu.setEnabled(True)
        else:
            self._gpu_status.setText("⚠ CPU mode (GPU not available or not working)")
            self._gpu_status.setStyleSheet("color: gray; font-size: 10px;")
            self._use_gpu.setEnabled(False)
            self._use_gpu.setChecked(False)

    def _create_general_tab(self) -> QWidget:
        """Create general settings tab."""
        widget = QWidget()
        layout = QFormLayout()
        layout.setFieldGrowthPolicy(QFormLayout.FieldGrowthPolicy.AllNonFixedFieldsGrow)

        # Auto-translate
        self._auto_translate = QCheckBox("Enable auto-translate")
        layout.addRow(self._auto_translate)

        # Interval
        self._interval = QSpinBox()
        self._interval.setRange(1, 300)
        self._interval.setSuffix(" seconds")
        self._interval.setValue(10)
        layout.addRow("Auto-translate Interval:", self._interval)

        # Minimize to tray
        self._minimize_tray = QCheckBox("Minimize to system tray")
        layout.addRow(self._minimize_tray)

        # Start minimized
        self._start_minimized = QCheckBox("Start minimized to tray")
        layout.addRow(self._start_minimized)

        # Clear area button
        clear_btn = QPushButton("Clear Selected Area")
        clear_btn.clicked.connect(self._clear_area)
        layout.addRow(clear_btn)

        widget.setLayout(layout)
        return widget

    def _load_settings(self):
        """Load settings into UI."""
        # Find and set source language
        source = self._settings.get("source_language", "auto")
        for i in range(self._source_lang.count()):
            if self._source_lang.itemData(i) == source:
                self._source_lang.setCurrentIndex(i)
                break

        # Target language
        target = self._settings.get("target_language", "en")
        for i in range(self._target_lang.count()):
            if self._target_lang.itemData(i) == target:
                self._target_lang.setCurrentIndex(i)
                break

        # Service
        service = self._settings.get("translation_service", "google")
        for i in range(self._service.count()):
            if self._service.itemData(i) == service:
                self._service.setCurrentIndex(i)
                break

        # OCR engine
        ocr = self._settings.get("ocr_engine", "tesseract")
        for i in range(self._ocr_engine.count()):
            if self._ocr_engine.itemData(i) == ocr:
                self._ocr_engine.setCurrentIndex(i)
                break

        # PSM mode
        psm = self._settings.get("ocr_psm_mode", "psm_6")
        for i in range(self._psm_mode.count()):
            if self._psm_mode.itemData(i) == psm:
                self._psm_mode.setCurrentIndex(i)
                break

        # Merge lines
        self._merge_lines.setChecked(self._settings.get("ocr_merge_lines", True))

        # GPU acceleration
        self._use_gpu.setChecked(self._settings.get("ocr_use_gpu", True))

        # Auto-translate
        self._auto_translate.setChecked(self._settings.get("auto_translate", False))
        self._interval.setValue(self._settings.get("auto_translate_interval", 10))
        self._minimize_tray.setChecked(self._settings.get("minimize_to_tray", True))
        self._start_minimized.setChecked(self._settings.get("start_minimized", False))

        # Trigger engine change to set correct PSM state
        self._on_engine_changed(0)

    def _save_and_accept(self):
        """Save settings and accept."""
        self._settings.set("source_language", self._source_lang.currentData())
        self._settings.set("target_language", self._target_lang.currentData())
        self._settings.set("translation_service", self._service.currentData())
        self._settings.set("ocr_engine", self._ocr_engine.currentData())
        self._settings.set("ocr_psm_mode", self._psm_mode.currentData())
        self._settings.set("ocr_merge_lines", self._merge_lines.isChecked())
        self._settings.set("ocr_use_gpu", self._use_gpu.isChecked())
        self._settings.set("auto_translate", self._auto_translate.isChecked())
        self._settings.set("auto_translate_interval", self._interval.value())
        self._settings.set("minimize_to_tray", self._minimize_tray.isChecked())
        self._settings.set("start_minimized", self._start_minimized.isChecked())
        self._settings.save()
        self.accept()

    def _clear_area(self):
        """Clear the saved capture area."""
        self._settings.set_capture_area(None)
        self._settings.save()

    def get_settings(self) -> dict:
        """Get current settings values."""
        return {
            "source_language": self._source_lang.currentData(),
            "target_language": self._target_lang.currentData(),
            "translation_service": self._service.currentData(),
            "ocr_engine": self._ocr_engine.currentData(),
            "auto_translate": self._auto_translate.isChecked(),
            "auto_translate_interval": self._interval.value(),
        }


class MainWindow(QMainWindow):
    """Main application window."""

    def __init__(self, settings: Settings, parent=None):
        super().__init__(parent)
        self._settings = settings
        self._auto_timer = QTimer()
        self._auto_timer.timeout.connect(self._auto_capture)
        self._area_selector = None
        self._tray = None

        self._setup_ui()
        self._setup_tray()
        self._load_settings()
        self._connect_signals()

    def _setup_ui(self):
        """Set up the UI."""
        self.setWindowTitle("TraRn - Screen Translator")
        self.setMinimumSize(500, 400)

        # Central widget
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout()
        central.setLayout(layout)

        # Source text (OCR result)
        source_group = QGroupBox("Original Text (OCR)")
        source_layout = QVBoxLayout()
        self._source_text = QTextEdit()
        self._source_text.setReadOnly(True)
        self._source_text.setPlaceholderText("Captured text will appear here...")
        source_layout.addWidget(self._source_text)
        source_group.setLayout(source_layout)
        layout.addWidget(source_group)

        # Target text (translation)
        target_group = QGroupBox("Translation")
        target_layout = QVBoxLayout()
        self._target_text = QTextEdit()
        self._target_text.setReadOnly(True)
        self._target_text.setPlaceholderText("Translation will appear here...")
        target_layout.addWidget(self._target_text)
        target_group.setLayout(target_layout)
        layout.addWidget(target_group)

        # Buttons
        btn_layout = QHBoxLayout()

        self._select_area_btn = QPushButton("📐 Select Area")
        self._select_area_btn.clicked.connect(self._show_area_selector)
        btn_layout.addWidget(self._select_area_btn)

        self._capture_btn = QPushButton("📸 Capture")
        self._capture_btn.clicked.connect(self._manual_capture)
        btn_layout.addWidget(self._capture_btn)

        self._auto_toggle_btn = QPushButton("⏸️ Auto: Off")
        self._auto_toggle_btn.setCheckable(True)
        self._auto_toggle_btn.clicked.connect(self._toggle_auto_translate)
        btn_layout.addWidget(self._auto_toggle_btn)

        self._settings_btn = QPushButton("⚙️ Settings")
        self._settings_btn.clicked.connect(self._show_settings)
        btn_layout.addWidget(self._settings_btn)

        layout.addLayout(btn_layout)

        # Status bar
        self._status_label = QLabel("Ready")
        self.statusBar().addPermanentWidget(self._status_label)

        # Keyboard shortcut for toggling auto-translate (F6)
        self._toggle_shortcut = QShortcut(QKeySequence("F6"), self)
        self._toggle_shortcut.activated.connect(self._toggle_auto_translate)

    def _setup_tray(self):
        """Set up system tray."""
        self._tray = SystemTray(self)
        if self._tray.setup():
            self._tray.show()
        else:
            self._status_label.setText("System tray not available")

    def _load_settings(self):
        """Load saved settings."""
        # Window geometry
        geom = self._settings.get_window_geometry()
        if geom:
            self.setGeometry(geom)

        # Auto-translate
        auto_enabled = self._settings.get("auto_translate", False)
        if auto_enabled:
            interval = self._settings.get("auto_translate_interval", 10) * 1000
            self._auto_timer.start(interval)
            if self._tray:
                self._tray.set_auto_translate_enabled(True)
        
        # Update button state
        self._update_auto_button(auto_enabled)

    def _connect_signals(self):
        """Connect signals."""
        # Tray signals
        if self._tray:
            self._tray.show_window.connect(self._show_from_tray)
            self._tray.hide_window.connect(self.hide)
            self._tray.capture_now.connect(self._manual_capture)
            self._tray.toggle_auto.connect(self._toggle_auto_translate)
            self._tray.show_settings.connect(self._show_settings)
            self._tray.show_about.connect(self._show_about)
            self._tray.quit_app.connect(self._quit_app)

    def _show_area_selector(self):
        """Show area selector overlay."""
        self._area_selector = AreaSelector()
        self._area_selector.area_selected.connect(self._on_area_selected)
        self._area_selector.selection_cancelled.connect(self._on_selection_cancelled)
        self._area_selector.showFullScreen()

    def _on_area_selected(self, rect: QRect):
        """Handle area selection."""
        self._settings.set_capture_area(rect)
        self._settings.save()
        self._status_label.setText(f"Area: {rect.width()}x{rect.height()} at ({rect.x()}, {rect.y()})")
        self._area_selector = None

        # Auto-capture if enabled
        if self._settings.get("auto_translate", False):
            self._manual_capture()

    def _on_selection_cancelled(self):
        """Handle selection cancellation."""
        self._area_selector = None
        self._status_label.setText("Selection cancelled")

    def _manual_capture(self):
        """Manual capture triggered by user."""
        self._do_capture()

    def _auto_capture(self):
        """Auto capture triggered by timer."""
        if self._settings.get("auto_translate", False):
            self._do_capture()

    def _do_capture(self):
        """Perform the actual capture."""
        area = self._settings.get_capture_area()
        if not area:
            self._status_label.setText("Please select an area first")
            if self._tray:
                self._tray.show_message("TraRn", "Please select a screen area first")
            return

        self._status_label.setText("Capturing...")

        # Capture
        self._capture = ScreenshotCapture()
        self._capture.capture_complete.connect(self._on_capture_complete)
        self._capture.capture_error.connect(self._on_capture_error)
        self._capture.capture_region(area)

    def _on_capture_complete(self, image):
        """Handle successful capture."""
        self._status_label.setText("Processing OCR...")

        # OCR
        self._ocr = OCREngine(
            engine=self._settings.get("ocr_engine", "tesseract"),
            psm_mode=self._settings.get("ocr_psm_mode", "psm_6"),
            merge_lines=self._settings.get("ocr_merge_lines", True),
            use_gpu=self._settings.get("ocr_use_gpu", True)
        )
        self._ocr.ocr_complete.connect(self._on_ocr_complete)
        self._ocr.ocr_error.connect(self._on_ocr_error)
        self._ocr.process(image)

    def _on_capture_error(self, error: str):
        """Handle capture error."""
        self._status_label.setText(f"Error: {error}")
        if self._tray:
            self._tray.show_message("Capture Error", error)

    def _on_ocr_complete(self, text: str):
        """Handle successful OCR."""
        self._source_text.setText(text)
        self._status_label.setText("Translating...")

        # Translate
        self._translator = Translator(service=self._settings.get("translation_service", "google"))
        self._translator.translation_complete.connect(self._on_translation_complete)
        self._translator.translation_error.connect(self._on_translation_error)
        self._translator.set_source_language(self._settings.get("source_language", "auto"))
        self._translator.set_target_language(self._settings.get("target_language", "en"))
        self._translator.translate(text)

    def _on_ocr_error(self, error: str):
        """Handle OCR error."""
        # Only show notification if not in auto mode (to avoid spam during gameplay)
        auto_enabled = self._settings.get("auto_translate", False)
        self._status_label.setText(f"OCR: No text found" if auto_enabled else f"OCR Error: {error}")
        if self._tray and not auto_enabled:
            self._tray.show_message("OCR Error", error)

    def _on_translation_complete(self, text: str):
        """Handle successful translation."""
        self._target_text.setText(text)
        self._status_label.setText("Ready")

    def _on_translation_error(self, error: str):
        """Handle translation error."""
        # Only show notification if not in auto mode (to avoid spam during gameplay)
        auto_enabled = self._settings.get("auto_translate", False)
        self._status_label.setText(f"Translation failed" if auto_enabled else f"Translation Error: {error}")
        if self._tray and not auto_enabled:
            self._tray.show_message("Translation Error", error)

    def _show_settings(self):
        """Show settings dialog."""
        dialog = SettingsDialog(self._settings, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            # Apply settings
            self._apply_settings()

    def _apply_settings(self):
        """Apply changed settings."""
        # Auto-translate timer
        auto_enabled = self._settings.get("auto_translate", False)
        if auto_enabled:
            interval = self._settings.get("auto_translate_interval", 10) * 1000
            self._auto_timer.start(interval)
        else:
            self._auto_timer.stop()

        if self._tray:
            self._tray.set_auto_translate_enabled(auto_enabled)
        
        self._update_auto_button(auto_enabled)

    def _toggle_auto_translate(self):
        """Toggle auto-translate from tray or button."""
        current = self._settings.get("auto_translate", False)
        self._settings.set("auto_translate", not current)
        self._settings.save()
        self._apply_settings()
        status = "ON" if not current else "OFF"
        # Show brief notification without error prefix
        self._status_label.setText(f"Auto-translate: {status}")
        # Also show tray notification
        if self._tray:
            self._tray.show_message("TraRn", f"Auto-translate turned {status}")
        self._update_auto_button(not current)

    def _update_auto_button(self, enabled: bool):
        """Update auto-translate button appearance."""
        if enabled:
            self._auto_toggle_btn.setText("▶️ Auto: On")
            self._auto_toggle_btn.setChecked(True)
        else:
            self._auto_toggle_btn.setText("⏸️ Auto: Off")
            self._auto_toggle_btn.setChecked(False)

    def _show_from_tray(self):
        """Show window from tray."""
        self.show()
        self.activateWindow()
        self.raise_()

    def _show_about(self):
        """Show about dialog."""
        dialog = AboutDialog(self)
        dialog.exec()

    def _quit_app(self):
        """Quit application."""
        self._save_geometry()
        from PyQt6.QtWidgets import QApplication
        QApplication.quit()

    def _save_geometry(self):
        """Save window geometry."""
        self._settings.set_window_geometry(self.geometry())
        self._settings.save()

    def closeEvent(self, event: QCloseEvent):
        """Handle window close."""
        if self._settings.get("minimize_to_tray", True) and self._tray and self._tray._tray_icon and self._tray._tray_icon.isVisible():
            event.ignore()
            self.hide()
            if self._tray:
                self._tray.show_message("TraRn", "Minimized to tray. Double-click to restore.")
        else:
            self._save_geometry()
            event.accept()
