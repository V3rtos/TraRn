"""Settings management module."""

import json
from pathlib import Path
from typing import Any, Optional

from PyQt6.QtCore import QObject, QRect


class Settings(QObject):
    """Application settings manager."""

    DEFAULTS = {
        "source_language": "auto",
        "target_language": "en",
        "ocr_engine": "tesseract",
        "ocr_psm_mode": "psm_6",
        "ocr_merge_lines": True,
        "ocr_use_gpu": True,
        "translation_service": "google",
        "auto_translate": False,
        "auto_translate_interval": 10,
        "capture_area": None,  # [x, y, width, height]
        "window_geometry": None,
        "minimize_to_tray": True,
        "start_minimized": False,
    }

    def __init__(self, parent=None, config_path: Optional[Path] = None):
        super().__init__(parent)
        if config_path is None:
            config_path = Path.home() / ".config" / "trarn" / "settings.json"
        self._config_path = config_path
        self._settings = self._load()

    def _load(self) -> dict:
        """Load settings from file."""
        if self._config_path.exists():
            try:
                with open(self._config_path, "r") as f:
                    saved = json.load(f)
                    # Merge with defaults
                    settings = self.DEFAULTS.copy()
                    settings.update(saved)
                    return settings
            except (json.JSONDecodeError, IOError):
                pass
        return self.DEFAULTS.copy()

    def save(self) -> None:
        """Save settings to file."""
        self._config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self._config_path, "w") as f:
            json.dump(self._settings, f, indent=2)

    def get(self, key: str, default: Any = None) -> Any:
        """Get a setting value."""
        return self._settings.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set a setting value."""
        self._settings[key] = value

    def get_capture_area(self) -> Optional[QRect]:
        """Get the saved capture area."""
        area = self._settings.get("capture_area")
        if area and len(area) == 4:
            return QRect(area[0], area[1], area[2], area[3])
        return None

    def set_capture_area(self, rect: Optional[QRect]) -> None:
        """Set the capture area."""
        if rect:
            self._settings["capture_area"] = [rect.x(), rect.y(), rect.width(), rect.height()]
        else:
            self._settings["capture_area"] = None

    def get_window_geometry(self) -> Optional[QRect]:
        """Get the saved window geometry."""
        geom = self._settings.get("window_geometry")
        if geom and len(geom) == 4:
            return QRect(geom[0], geom[1], geom[2], geom[3])
        return None

    def set_window_geometry(self, rect: Optional[QRect]) -> None:
        """Set the window geometry."""
        if rect:
            self._settings["window_geometry"] = [rect.x(), rect.y(), rect.width(), rect.height()]
        else:
            self._settings["window_geometry"] = None

    def reset(self) -> None:
        """Reset settings to defaults."""
        self._settings = self.DEFAULTS.copy()
        self.save()
