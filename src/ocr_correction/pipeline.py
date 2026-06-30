"""
Core OCR processing pipeline.

Uses Dependency Injection to decouple the core pipeline from
specific ML frameworks (Tesseract, NLTK, LanguageTool).
"""

import structlog
from math import floor

import cv2
import numpy as np
from PIL import Image

from ocr_correction.config import settings
from ocr_correction.domain import Document
from ocr_correction.ports import BaseOCREngine, BaseNLPProcessor, BaseSpellingEngine

logger = structlog.get_logger(__name__)

def preprocess_image(pil_img: Image.Image) -> Image.Image:
    """
    Image pre-processing pipeline designed to maximise OCR accuracy:

    1. Convert to grayscale
    2. Apply fast non-local means denoising
    3. Binarise with adaptive Gaussian thresholding

    Returns a PIL Image ready for Tesseract.
    """
    gray = np.array(pil_img.convert("L"))
    denoised = cv2.fastNlMeansDenoising(gray, h=10)
    binary = cv2.adaptiveThreshold(
        denoised,
        255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11,
        2,
    )
    return Image.fromarray(binary)

def maybe_resize(pil_img: Image.Image, raw_bytes: bytes) -> Image.Image:
    """Downscale the image if it exceeds the size threshold."""
    if (len(raw_bytes) / (1024 * 1024)) > settings.image_size_threshold_mb:
        w, h = pil_img.size
        pil_img = pil_img.resize(
            (floor(w * settings.resize_factor), floor(h * settings.resize_factor)),
            Image.Resampling.LANCZOS,
        )
        logger.info("Image resized to %s", pil_img.size)
    return pil_img

class OCRPipeline:
    """
    End-to-end OCR and spelling correction pipeline.

    Operates using injected Adapters for OCR, NLP, and Spelling.
    """

    def __init__(
        self,
        ocr_engine: BaseOCREngine,
        nlp_processor: BaseNLPProcessor,
        spelling_engine: BaseSpellingEngine
    ):
        self.ocr_engine = ocr_engine
        self.nlp_processor = nlp_processor
        self.spelling_engine = spelling_engine

    def process(self, pil_img: Image.Image, lang_hint: str = "auto") -> Document:
        """
        Process the image through the pipeline.

        Returns a rich Document domain object.
        """
        preprocessed = preprocess_image(pil_img)

        raw_text = self.ocr_engine.extract_text(preprocessed)
        logger.info("OCR extracted %d characters", len(raw_text))

        tokenized = self.nlp_processor.tokenize(raw_text)

        if lang_hint == "auto":
            lang_code = self.nlp_processor.detect_language(tokenized)
        else:
            lang_code = settings.language_map.get(lang_hint, settings.default_lang_code)

        corrected = self.spelling_engine.correct(tokenized, lang_code)
        logger.info("Spelling correction complete (lang=%s)", lang_code)

        return Document(
            raw_text=raw_text,
            corrected_text=corrected,
            detected_language=lang_code
        )

# For backward compatibility with routes that haven't been refactored yet
# we can instantiate a default pipeline.
def default_ocr_pipeline(pil_img: Image.Image, lang_hint: str = "auto") -> tuple:
    from ocr_correction.adapters import TesseractAdapter, NLTKProcessor, LanguageToolAdapter
    pipeline = OCRPipeline(
        ocr_engine=TesseractAdapter(),
        nlp_processor=NLTKProcessor(),
        spelling_engine=LanguageToolAdapter()
    )
    doc = pipeline.process(pil_img, lang_hint)
    return doc.raw_text, doc.corrected_text, doc.detected_language

# The routes still look for `ocr_pipeline` function.
ocr_pipeline = default_ocr_pipeline
