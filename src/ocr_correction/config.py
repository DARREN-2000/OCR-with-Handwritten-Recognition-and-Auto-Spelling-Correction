"""
Configuration settings for the OCR pipeline.
"""

from typing import Dict
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    """Application settings, loaded from environment variables."""

    # Image processing
    image_size_threshold_mb: float = Field(default=2.0, description="Max MB before resizing.")
    resize_factor: float = Field(default=0.9, description="Factor to resize image by.")

    # Tesseract OCR
    ocr_config: str = Field(
        default="--oem 1 --psm 3",
        description="Tesseract configuration string.")

    # Language support
    language_map: Dict[str, str] = Field(
        default={
            "en": "en-US",
            "fr": "fr",
            "de": "de-DE",
            "es": "es",
            "pt": "pt-PT",
        },
        description="Maps ISO-639-1 codes returned by langdetect to LanguageTool locale codes."
    )
    default_lang_code: str = Field(default="en-US", description="Fallback language code.")

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()

# Backwards compatibility for now (we'll phase these out where possible)
IMAGE_SIZE_THRESHOLD_MB = settings.image_size_threshold_mb
RESIZE_FACTOR = settings.resize_factor
OCR_CONFIG = settings.ocr_config
LANGUAGE_MAP = settings.language_map
DEFAULT_LANG_CODE = settings.default_lang_code
