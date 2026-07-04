class OCRError(Exception):
    """Base class for all OCR pipeline exceptions."""
    pass


class InvalidImageError(OCRError):
    """Raised when the uploaded image is invalid, corrupt, or an unsupported type."""
    pass


class LanguageDetectionError(OCRError):
    """Raised when the language of the text cannot be determined."""
    pass


class EngineError(OCRError):
    """Raised when an external ML/OCR engine fails."""
    pass


class PaddleOCRError(EngineError):
    """Raised when PaddleOCR fails."""
    pass


class TrOCRError(EngineError):
    """Raised when TrOCR fails."""
    pass


class TesseractError(EngineError):
    """Raised when Tesseract OCR fails."""
    pass


class NLTKError(EngineError):
    """Raised when NLTK processing fails."""
    pass


class LanguageToolError(EngineError):
    """Raised when LanguageTool processing fails."""
    pass
