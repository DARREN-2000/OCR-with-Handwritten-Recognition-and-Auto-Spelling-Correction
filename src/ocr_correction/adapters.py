import os
import sys
import functools
import structlog

import nltk
import pytesseract
import language_tool_python
from langdetect import LangDetectException, detect
from nltk.tokenize import sent_tokenize, word_tokenize
from PIL import Image

from ocr_correction.ports import BaseOCREngine, BaseNLPProcessor, BaseSpellingEngine
from ocr_correction.config import settings
from ocr_correction.exceptions import EngineError, LanguageDetectionError

logger = structlog.get_logger(__name__)

# Pre-load NLTK data
for _resource in ("tokenizers/punkt", "tokenizers/punkt_tab"):
    try:
        nltk.data.find(_resource)
    except LookupError:
        nltk.download(_resource.split("/")[-1], quiet=True)

# Tesseract path config for Windows
if sys.platform == "win32":
    _win_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(_win_path):
        pytesseract.pytesseract.tesseract_cmd = _win_path

class TesseractAdapter(BaseOCREngine):
    """Adapter for Tesseract OCR."""

    def extract_text(self, image: Image.Image) -> str:
        try:
            return pytesseract.image_to_string(image, config=settings.ocr_config)
        except Exception as exc:
            raise EngineError(f"Tesseract extraction failed: {exc}") from exc

class NLTKProcessor(BaseNLPProcessor):
    """Adapter for NLTK tokenization and langdetect."""

    def tokenize(self, text: str) -> str:
        try:
            sentences = sent_tokenize(text)
            return "\n".join(" ".join(word_tokenize(s)) for s in sentences)
        except Exception as exc:
            raise EngineError(f"NLTK tokenization failed: {exc}") from exc

    def detect_language(self, text: str) -> str:
        if not text.strip():
            return settings.default_lang_code
        try:
            code = detect(text)
            return settings.language_map.get(code, settings.default_lang_code)
        except LangDetectException:
            # Fall back to default instead of crashing
            return settings.default_lang_code
        except Exception as exc:
            raise LanguageDetectionError(f"Language detection failed: {exc}") from exc

@functools.lru_cache(maxsize=4)
def _get_cached_language_tool(lang_code: str):
    """Module-level cache to ensure LanguageTool is shared across instances."""
    return language_tool_python.LanguageTool(lang_code)

class LanguageToolAdapter(BaseSpellingEngine):
    """Adapter for LanguageTool spelling and grammar correction."""

    def correct(self, text: str, lang_code: str) -> str:
        if not text.strip():
            return text
        try:
            tool = _get_cached_language_tool(lang_code)
            return tool.correct(text)
        except Exception as exc:
            raise EngineError(f"LanguageTool correction failed: {exc}") from exc
