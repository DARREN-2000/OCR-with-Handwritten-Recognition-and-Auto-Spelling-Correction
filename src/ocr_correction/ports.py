from abc import ABC, abstractmethod
from typing import Optional
from PIL import Image

class BaseOCREngine(ABC):
    """Abstract base class (Port) for OCR engines."""

    @abstractmethod
    def extract_text(self, image: Image.Image) -> str:
        """Extract text from a PIL Image."""
        pass

class BaseNLPProcessor(ABC):
    """Abstract base class (Port) for NLP tokenization and language detection."""

    @abstractmethod
    def tokenize(self, text: str) -> str:
        """Tokenize text into a normalized format."""
        pass

    @abstractmethod
    def detect_language(self, text: str) -> str:
        """Detect language of the text, returning a locale code."""
        pass

class BaseSpellingEngine(ABC):
    """Abstract base class (Port) for spelling/grammar correction engines."""

    @abstractmethod
    def correct(self, text: str, lang_code: str) -> str:
        """Correct spelling and grammar for the given text and language."""
        pass
