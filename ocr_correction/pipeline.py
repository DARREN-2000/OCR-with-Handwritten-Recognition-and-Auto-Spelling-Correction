"""
Core OCR processing pipeline.

Combines image pre-processing, Tesseract OCR, NLTK tokenization,
language detection, and LanguageTool correction into a single pipeline.
"""

import os
import sys
import logging
from math import floor

import cv2
import nltk
import numpy as np
import language_tool_python
import pytesseract
from langdetect import LangDetectException, detect
from nltk.tokenize import sent_tokenize, word_tokenize
from PIL import Image

from ocr_correction.config import (
    IMAGE_SIZE_THRESHOLD_MB,
    RESIZE_FACTOR,
    OCR_CONFIG,
    LANGUAGE_MAP,
    DEFAULT_LANG_CODE,
)

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# NLTK data – download only when the resource is not already present
# ---------------------------------------------------------------------------
for _resource in ("tokenizers/punkt", "tokenizers/punkt_tab"):
    try:
        nltk.data.find(_resource)
    except LookupError:
        nltk.download(_resource.split("/")[-1], quiet=True)

# ---------------------------------------------------------------------------
# Tesseract path (Windows only – Linux/macOS find it on PATH automatically)
# ---------------------------------------------------------------------------
if sys.platform == "win32":
    _win_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(_win_path):
        pytesseract.pytesseract.tesseract_cmd = _win_path


def preprocess_image(pil_img: Image.Image) -> Image.Image:
    """
    Image pre-processing pipeline designed to maximise OCR accuracy:

    1. Convert to grayscale
    2. Apply fast non-local means denoising
    3. Binarise with adaptive Gaussian thresholding

    Returns a PIL Image ready for Tesseract.
    """
    arr = np.array(pil_img)
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY) if arr.ndim == 3 else arr
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
    if (len(raw_bytes) / (1024 * 1024)) > IMAGE_SIZE_THRESHOLD_MB:
        w, h = pil_img.size
        pil_img = pil_img.resize(
            (floor(w * RESIZE_FACTOR), floor(h * RESIZE_FACTOR)),
            Image.LANCZOS,
        )
        logger.info("Image resized to %s", pil_img.size)
    return pil_img


def detect_language(text: str) -> str:
    """
    Detect the dominant language of *text* and return the corresponding
    LanguageTool locale string.  Falls back to English on any failure.
    """
    try:
        code = detect(text)
        return LANGUAGE_MAP.get(code, DEFAULT_LANG_CODE)
    except LangDetectException:
        return DEFAULT_LANG_CODE


def tokenize(text: str) -> str:
    """
    Sentence-segment and word-tokenize the raw OCR output with NLTK,
    then re-join so the language model receives well-formed input.
    """
    sentences = sent_tokenize(text)
    return "\n".join(" ".join(word_tokenize(s)) for s in sentences)


def apply_language_model(text: str, lang_code: str = DEFAULT_LANG_CODE) -> str:
    """
    Run LanguageTool's grammar / spelling language model over *text*
    and return the corrected string.
    """
    tool = language_tool_python.LanguageTool(lang_code)
    try:
        return tool.correct(text)
    finally:
        tool.close()


def ocr_pipeline(pil_img: Image.Image, lang_hint: str = "auto") -> tuple:
    """
    Full end-to-end pipeline:
      preprocess → OCR → tokenize → detect language → language-model correction

    Returns (raw_text, corrected_text, detected_lang_code).
    """
    preprocessed = preprocess_image(pil_img)
    raw_text = pytesseract.image_to_string(preprocessed, config=OCR_CONFIG)
    logger.info("OCR extracted %d characters", len(raw_text))

    tokenized = tokenize(raw_text)

    if lang_hint == "auto":
        lang_code = detect_language(tokenized)
    else:
        lang_code = LANGUAGE_MAP.get(lang_hint, DEFAULT_LANG_CODE)

    corrected = apply_language_model(tokenized, lang_code)
    logger.info("Spelling correction complete (lang=%s)", lang_code)

    return raw_text, corrected, lang_code
