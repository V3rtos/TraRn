"""OCR module for text extraction from images."""

import re
from typing import Optional, Tuple

from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QImage


class OCREngine(QObject):
    """OCR engine with multiple backend support."""

    ocr_complete = pyqtSignal(str)
    ocr_error = pyqtSignal(str)

    # Tesseract PSM (Page Segmentation Mode) descriptions
    PSM_MODES = {
        "psm_3": ("Fully Automatic", "Fully automatic page segmentation, no OSD"),
        "psm_4": ("Single Column", "Assume a single column of text of variable sizes"),
        "psm_6": ("Uniform Block", "Assume a single uniform block of text (default)"),
        "psm_7": ("Single Line", "Treat the image as a single text line"),
        "psm_11": ("Sparse Text", "Find sparse text, no assumptions about order"),
        "psm_12": ("Sparse Text + OSD", "Sparse text with OSD"),
    }

    @staticmethod
    def detect_gpu() -> Tuple[bool, str]:
        """
        Detect if GPU is available for OCR acceleration.

        Returns:
            Tuple of (gpu_available, gpu_name)
        """
        # Check for CUDA (NVIDIA GPU)
        try:
            import torch
            if torch.cuda.is_available():
                gpu_name = torch.cuda.get_device_name(0)
                return True, f"CUDA ({gpu_name})"
        except ImportError:
            pass

        # Check for ROCm (AMD GPU) - only if torch has ROCm support
        try:
            import torch
            # Check if this is a ROCm build
            is_rocm = ('rocm' in torch.__version__.lower() or 
                       (hasattr(torch.version, 'hip') and torch.version.hip is not None) or
                       (hasattr(torch, 'has_hip') and torch.has_hip))
            
            if is_rocm:
                # Try to actually use GPU to verify it works
                try:
                    # Test if we can actually access GPU
                    test_tensor = torch.zeros(1).to('cuda')
                    del test_tensor
                    return True, "ROCm (AMD GPU)"
                except (RuntimeError, ImportError, OSError) as e:
                    # ROCm installed but not working - return CPU
                    pass
        except ImportError:
            pass

        # Check for Apple Metal (MPS)
        try:
            import torch
            if hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
                return True, "Metal (Apple Silicon)"
        except (ImportError, AttributeError):
            pass

        return False, "Not detected"

    def __init__(self, parent=None, engine: str = "tesseract", psm_mode: str = "psm_6", merge_lines: bool = True, use_gpu: bool = True):
        """
        Initialize OCR engine.

        Args:
            parent: Parent QObject.
            engine: OCR engine to use ('tesseract', 'easyocr', 'paddleocr').
            psm_mode: Tesseract PSM mode (e.g., 'psm_6').
            merge_lines: Whether to merge lines for better translation.
            use_gpu: Whether to use GPU acceleration (for EasyOCR/PaddleOCR).
        """
        super().__init__(parent)
        self._engine = engine
        self._language = "en"
        self._psm_mode = psm_mode
        self._merge_lines = merge_lines
        self._use_gpu = use_gpu

    def set_language(self, lang: str) -> None:
        """Set OCR language."""
        self._language = lang

    def set_psm_mode(self, mode: str) -> None:
        """Set Tesseract PSM mode."""
        self._psm_mode = mode

    def set_merge_lines(self, merge: bool) -> None:
        """Enable/disable line merging."""
        self._merge_lines = merge

    def set_use_gpu(self, use_gpu: bool) -> None:
        """Enable/disable GPU acceleration."""
        self._use_gpu = use_gpu

    def process(self, image: QImage) -> None:
        """
        Extract text from image.

        Args:
            image: QImage to process.
        """
        if self._engine == "easyocr":
            self._process_easyocr(image)
        elif self._engine == "paddleocr":
            try:
                self._process_paddleocr(image)
            except ImportError:
                self.ocr_error.emit("PaddleOCR not installed. Install with: pip install paddlepaddle paddleocr")
        else:
            self._process_tesseract(image)

    def _postprocess_text(self, text: str) -> str:
        """
        Postprocess OCR text to improve translation quality.

        - Merges lines that are part of the same sentence
        - Preserves paragraph breaks (double newlines)
        - Removes extra whitespace
        """
        if not self._merge_lines:
            return text.strip()

        lines = text.split('\n')
        result_lines = []
        current_paragraph = []

        for line in lines:
            line = line.strip()
            if not line:
                # Empty line - end of paragraph
                if current_paragraph:
                    result_lines.append(' '.join(current_paragraph))
                    current_paragraph = []
                result_lines.append('')  # Preserve paragraph break
            else:
                current_paragraph.append(line)

        # Don't forget the last paragraph
        if current_paragraph:
            result_lines.append(' '.join(current_paragraph))

        # Remove trailing empty lines and clean up
        result = '\n'.join(result_lines).strip()

        # Clean up multiple spaces
        result = re.sub(r' +', ' ', result)

        return result

    def _process_tesseract(self, image: QImage) -> None:
        """Process using Tesseract OCR."""
        try:
            import pytesseract
            from PIL import Image
            from PyQt6.QtCore import QBuffer, QIODevice

            # Convert QImage to PIL Image using QBuffer
            buffer = QBuffer()
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            image.save(buffer, "PNG")

            # Load PNG data into PIL
            from io import BytesIO
            pil_image = Image.open(BytesIO(buffer.data()))

            # Perform OCR
            lang_map = {
                "en": "eng",
                "ru": "rus",
                "de": "deu",
                "fr": "fra",
                "es": "spa",
                "it": "ita",
                "pt": "por",
                "zh": "chi_sim",
                "ja": "jpn",
                "ko": "kor",
            }
            tesseract_lang = lang_map.get(self._language, "eng")

            # Get PSM mode number (e.g., 'psm_6' -> '6')
            psm_num = self._psm_mode.replace('psm_', '')

            text = pytesseract.image_to_string(
                pil_image,
                lang=tesseract_lang,
                config=f"--psm {psm_num}"
            )

            if text.strip():
                # Apply postprocessing
                processed_text = self._postprocess_text(text)
                self.ocr_complete.emit(processed_text)
            else:
                self.ocr_error.emit("No text detected in image")

        except ImportError:
            self.ocr_error.emit("pytesseract not installed. Install with: pip install pytesseract")
        except Exception as e:
            self.ocr_error.emit(f"OCR failed: {str(e)}")

    def _process_easyocr(self, image: QImage) -> None:
        """Process using EasyOCR."""
        try:
            import easyocr
            import numpy as np
            from PIL import Image
            from PyQt6.QtCore import QBuffer, QIODevice
            import warnings

            # Suppress torch warnings about CPU/GPU
            warnings.filterwarnings('ignore', category=UserWarning)

            # Convert QImage to PIL Image using QBuffer
            buffer = QBuffer()
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            image.save(buffer, "PNG")

            # Load PNG data into PIL then numpy
            from io import BytesIO
            pil_image = Image.open(BytesIO(buffer.data()))
            np_array = np.array(pil_image)

            # Map language codes
            lang_map = {
                "en": "en",
                "ru": "ru",
                "de": "de",
                "fr": "fr",
                "es": "es",
                "it": "it",
                "pt": "pt",
                "zh": "ch_sim",
                "ja": "ja",
                "ko": "ko",
            }
            easyocr_lang = lang_map.get(self._language, "en")

            # Use GPU if enabled and available
            reader = easyocr.Reader([easyocr_lang], gpu=self._use_gpu, verbose=False)
            results = reader.readtext(np_array, detail=0)

            if results:
                text = "\n".join(results)
                # Apply postprocessing
                processed_text = self._postprocess_text(text)
                self.ocr_complete.emit(processed_text)
            else:
                self.ocr_error.emit("No text detected in image")

        except ImportError:
            self.ocr_error.emit("easyocr not installed. Install with: pip install easyocr")
        except Exception as e:
            self.ocr_error.emit(f"OCR failed: {str(e)}")

    def _process_paddleocr(self, image: QImage) -> None:
        """Process using PaddleOCR."""
        try:
            from paddleocr import PaddleOCR
            import numpy as np
            from PIL import Image
            from PyQt6.QtCore import QBuffer, QIODevice
            import warnings

            # Suppress warnings
            warnings.filterwarnings('ignore', category=UserWarning)

            # Convert QImage to PIL Image using QBuffer
            buffer = QBuffer()
            buffer.open(QIODevice.OpenModeFlag.WriteOnly)
            image.save(buffer, "PNG")

            # Load PNG data into PIL then numpy
            from io import BytesIO
            pil_image = Image.open(BytesIO(buffer.data()))
            np_array = np.array(pil_image)

            # Map language codes
            lang_map = {
                "en": "en",
                "ru": "ru",
                "de": "german",
                "fr": "french",
                "es": "spanish",
                "it": "italian",
                "pt": "portuguese",
                "zh": "ch",
                "ja": "japan",
                "ko": "korean",
            }
            paddle_lang = lang_map.get(self._language, "en")

            # Initialize PaddleOCR with GPU setting
            ocr = PaddleOCR(lang=paddle_lang, use_gpu=self._use_gpu, show_log=False, verbose=False)
            results = ocr.ocr(np_array, cls=False)

            # Extract text from results
            texts = []
            if results and results[0]:
                for line in results[0]:
                    if line and len(line) >= 2:
                        text = line[1][0]
                        texts.append(text)

            if texts:
                text = "\n".join(texts)
                # Apply postprocessing
                processed_text = self._postprocess_text(text)
                self.ocr_complete.emit(processed_text)
            else:
                self.ocr_error.emit("No text detected in image")

        except ImportError:
            self.ocr_error.emit("paddleocr not installed. Install with: pip install paddlepaddle paddleocr")
        except Exception as e:
            self.ocr_error.emit(f"OCR failed: {str(e)}")
