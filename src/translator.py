"""Translation module with multiple backend support."""

from typing import Optional

from PyQt6.QtCore import QObject, pyqtSignal


class Translator(QObject):
    """Text translation engine."""

    translation_complete = pyqtSignal(str)
    translation_error = pyqtSignal(str)

    # Language codes for deep-translator
    LANGUAGES = {
        "English": "en",
        "Russian": "ru",
        "German": "de",
        "French": "fr",
        "Spanish": "es",
        "Italian": "it",
        "Portuguese": "pt",
        "Chinese (Simplified)": "zh-CN",
        "Japanese": "ja",
        "Korean": "ko",
        "Polish": "pl",
        "Dutch": "nl",
        "Turkish": "tr",
        "Arabic": "ar",
        "Hindi": "hi",
    }

    def __init__(self, parent=None, service: str = "google"):
        """
        Initialize translator.
        
        Args:
            parent: Parent QObject.
            service: Translation service ('google', 'deepl', 'linguee').
        """
        super().__init__(parent)
        self._service = service
        self._source_lang = "auto"
        self._target_lang = "en"

    def set_source_language(self, lang: str) -> None:
        """Set source language ('auto' for auto-detect)."""
        self._source_lang = lang

    def set_target_language(self, lang: str) -> None:
        """Set target language."""
        self._target_lang = lang

    def set_service(self, service: str) -> None:
        """Set translation service."""
        self._service = service

    def translate(self, text: str) -> None:
        """
        Translate text.
        
        Args:
            text: Text to translate.
        """
        if not text.strip():
            self.translation_error.emit("No text to translate")
            return

        if self._service == "google":
            self._translate_google(text)
        elif self._service == "deepl":
            self._translate_deepl(text)
        else:
            self._translate_google(text)

    def _translate_google(self, text: str) -> None:
        """Translate using Google Translate."""
        try:
            from deep_translator import GoogleTranslator

            translator = GoogleTranslator(
                source=self._source_lang,
                target=self._target_lang
            )
            translated = translator.translate(text)

            if translated:
                self.translation_complete.emit(translated)
            else:
                self.translation_error.emit("Translation returned empty result")

        except ImportError:
            self.translation_error.emit(
                "deep-translator not installed. Install with: pip install deep-translator"
            )
        except Exception as e:
            self.translation_error.emit(f"Translation failed: {str(e)}")

    def _translate_deepl(self, text: str) -> None:
        """Translate using DeepL."""
        try:
            from deep_translator import DeepLTranslator
            import os

            api_key = os.environ.get("DEEPL_API_KEY")
            if not api_key:
                self.translation_error.emit(
                    "DeepL API key not set. Set DEEPL_API_KEY environment variable."
                )
                return

            translator = DeepLTranslator(
                source=self._source_lang,
                target=self._target_lang,
                api_key=api_key
            )
            translated = translator.translate(text)

            if translated:
                self.translation_complete.emit(translated)
            else:
                self.translation_error.emit("Translation returned empty result")

        except ImportError:
            self.translation_error.emit(
                "deep-translator not installed. Install with: pip install deep-translator"
            )
        except Exception as e:
            self.translation_error.emit(f"DeepL translation failed: {str(e)}")

    @classmethod
    def get_available_languages(cls) -> dict:
        """Get available languages."""
        return cls.LANGUAGES.copy()
