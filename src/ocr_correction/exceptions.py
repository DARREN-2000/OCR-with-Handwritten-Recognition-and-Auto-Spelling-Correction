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
