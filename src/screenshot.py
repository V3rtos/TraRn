"""Screenshot capture module with Wayland and X11 support."""

import subprocess
import tempfile
from pathlib import Path
from typing import Optional

from PyQt6.QtCore import QRect, QObject, pyqtSignal, QThread
from PyQt6.QtGui import QImage


class ScreenshotCapture(QObject):
    """Capture screenshots with Wayland and X11 support."""

    capture_complete = pyqtSignal(QImage)
    capture_error = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._temp_dir = Path(tempfile.gettempdir()) / "trarn"
        self._temp_dir.mkdir(exist_ok=True)

    def capture_region(self, rect: QRect) -> None:
        """
        Capture a screen region.
        
        Args:
            rect: The region to capture in global coordinates.
        """
        x, y, width, height = rect.x(), rect.y(), rect.width(), rect.height()

        if self._is_wayland():
            self._capture_wayland(x, y, width, height)
        else:
            self._capture_x11(x, y, width, height)

    def _is_wayland(self) -> bool:
        """Detect if running under Wayland."""
        session_type = subprocess.run(
            ["bash", "-c", "echo $XDG_SESSION_TYPE"],
            capture_output=True,
            text=True
        ).stdout.strip().lower()
        return session_type == "wayland"

    def _capture_wayland(self, x: int, y: int, width: int, height: int) -> None:
        """Capture using Wayland-compatible methods."""
        desktop = self._get_desktop_environment()
        
        # KDE Plasma - use kwin-screenshot or dbus
        if desktop in ["kde", "plasma"]:
            self._capture_kde_wayland(x, y, width, height)
        # wlroots (sway, river, etc.) - use grim
        elif self._command_exists("grim"):
            self._capture_with_grim(x, y, width, height)
        else:
            self.capture_error.emit(
                "No Wayland screenshot method found for this desktop environment."
            )

    def _get_desktop_environment(self) -> str:
        """Detect desktop environment."""
        desktop = subprocess.run(
            ["bash", "-c", "echo $XDG_CURRENT_DESKTOP"],
            capture_output=True,
            text=True
        ).stdout.strip().lower()
        return desktop

    def _capture_kde_wayland(self, x: int, y: int, width: int, height: int) -> None:
        """Capture on KDE Wayland using spectacle."""
        temp_file = self._temp_dir / "screenshot.png"
        
        try:
            # spectacle -b (batch/non-interactive) -n (no notifications)
            # -f (fullscreen) -o (output file)
            # On KDE Wayland, spectacle is the most reliable method
            result = subprocess.run(
                ["spectacle", "-b", "-n", "-f", "-o", str(temp_file)],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and temp_file.exists():
                # Crop to the selected region
                self._crop_and_emit(temp_file, x, y, width, height)
            else:
                self.capture_error.emit(
                    f"Spectacle failed: {result.stderr if result.stderr else 'Unknown error'}"
                )
        except subprocess.TimeoutExpired:
            self.capture_error.emit("Screenshot timeout")
        except Exception as e:
            self.capture_error.emit(str(e))

    def _capture_with_grim(self, x: int, y: int, width: int, height: int) -> None:
        """Capture using grim (Wayland, wlroots)."""
        temp_file = self._temp_dir / "screenshot.png"
        
        try:
            # grim -g geometry format: "x,y WxH"
            geom = f"{x},{y} {width}x{height}"
            result = subprocess.run(
                ["grim", "-g", geom, str(temp_file)],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and temp_file.exists():
                self._load_and_emit(temp_file)
            else:
                self.capture_error.emit(f"grim failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            self.capture_error.emit("Screenshot timeout")
        except Exception as e:
            self.capture_error.emit(str(e))

    def _capture_x11(self, x: int, y: int, width: int, height: int) -> None:
        """Capture using X11 methods."""
        if self._command_exists("maim"):
            self._capture_with_maim(x, y, width, height)
        elif self._command_exists("import"):
            self._capture_with_import(x, y, width, height)
        else:
            self.capture_error.emit(
                "No X11 screenshot tool found. Install 'maim' or ImageMagick."
            )

    def _capture_with_maim(self, x: int, y: int, width: int, height: int) -> None:
        """Capture using maim (X11)."""
        temp_file = self._temp_dir / "screenshot.png"
        
        try:
            result = subprocess.run(
                [
                    "maim",
                    "-x", str(x),
                    "-y", str(y),
                    "-w", str(width),
                    "-h", str(height),
                    str(temp_file)
                ],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and temp_file.exists():
                self._load_and_emit(temp_file)
            else:
                self.capture_error.emit(f"maim failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            self.capture_error.emit("Screenshot timeout")
        except Exception as e:
            self.capture_error.emit(str(e))

    def _capture_with_import(self, x: int, y: int, width: int, height: int) -> None:
        """Capture using ImageMagick import (X11)."""
        temp_file = self._temp_dir / "screenshot.png"
        
        try:
            result = subprocess.run(
                [
                    "import",
                    "-window", "root",
                    "-crop", f"{width}x{height}+{x}+{y}",
                    str(temp_file)
                ],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0 and temp_file.exists():
                self._load_and_emit(temp_file)
            else:
                self.capture_error.emit(f"import failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            self.capture_error.emit("Screenshot timeout")
        except Exception as e:
            self.capture_error.emit(str(e))

    def _load_and_emit(self, file_path: Path) -> None:
        """Load image from file and emit signal."""
        try:
            image = QImage()
            if image.load(str(file_path)):
                self.capture_complete.emit(image)
            else:
                self.capture_error.emit("Failed to load captured image")
        finally:
            # Clean up temp file
            if file_path.exists():
                file_path.unlink()

    def _crop_and_emit(self, file_path: Path, x: int, y: int, width: int, height: int) -> None:
        """Crop image to region and emit."""
        try:
            from PIL import Image

            # Open and crop the image
            with Image.open(file_path) as img:
                cropped = img.crop((x, y, x + width, y + height))
                
                # Save to bytes and load into QImage
                import io
                buffer = io.BytesIO()
                cropped.save(buffer, format="PNG")
                buffer.seek(0)
                
                image = QImage()
                if image.loadFromData(buffer.getvalue()):
                    self.capture_complete.emit(image)
                else:
                    self.capture_error.emit("Failed to load cropped image")
                
        except Exception as e:
            self.capture_error.emit(f"Crop failed: {str(e)}")
        finally:
            # Clean up temp file
            if file_path.exists():
                file_path.unlink()

    def _command_exists(self, cmd: str) -> bool:
        """Check if a command exists in PATH."""
        return subprocess.run(
            ["which", cmd],
            capture_output=True
        ).returncode == 0
