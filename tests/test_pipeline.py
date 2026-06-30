"""Unit tests for the OCR pipeline functions."""

import numpy as np
from PIL import Image

from ocr_correction.config import settings
from ocr_correction.pipeline import (
    maybe_resize,
    preprocess_image,
    OCRPipeline,
)
from ocr_correction.ports import BaseOCREngine, BaseNLPProcessor, BaseSpellingEngine

class MockOCREngine(BaseOCREngine):
    def extract_text(self, image: Image.Image) -> str:
        return "Mock extracted text."

class MockNLPProcessor(BaseNLPProcessor):
    def tokenize(self, text: str) -> str:
        return text.strip()

    def detect_language(self, text: str) -> str:
        return settings.default_lang_code

class MockSpellingEngine(BaseSpellingEngine):
    def correct(self, text: str, lang_code: str) -> str:
        return "Mock corrected text."

class TestPreprocessImage:
    """Tests for the preprocess_image function."""

    def test_returns_pil_image(self):
        img = Image.new("RGB", (100, 100), color=(128, 128, 128))
        result = preprocess_image(img)
        assert isinstance(result, Image.Image)

    def test_output_is_grayscale(self):
        img = Image.new("RGB", (100, 100), color=(128, 128, 128))
        result = preprocess_image(img)
        arr = np.array(result)
        assert arr.ndim == 2, "Preprocessed image should be 2D (grayscale)"

    def test_handles_grayscale_input(self):
        img = Image.new("L", (100, 100), color=128)
        result = preprocess_image(img)
        assert isinstance(result, Image.Image)

    def test_output_is_binary(self):
        img = Image.new("RGB", (100, 100), color=(128, 128, 128))
        result = preprocess_image(img)
        arr = np.array(result)
        unique_values = set(np.unique(arr))
        assert unique_values.issubset({0, 255}), (
            "Adaptive threshold should produce binary output"
        )


class TestMaybeResize:
    """Tests for the maybe_resize function."""

    def test_small_image_unchanged(self):
        img = Image.new("RGB", (100, 100))
        small_bytes = b"\x00" * 1024  # 1 KB
        result = maybe_resize(img, small_bytes)
        assert result.size == (100, 100)

    def test_large_image_resized(self):
        img = Image.new("RGB", (1000, 1000))
        large_bytes = b"\x00" * (3 * 1024 * 1024)  # 3 MB
        result = maybe_resize(img, large_bytes)
        assert result.size[0] < 1000
        assert result.size[1] < 1000


class TestOCRPipeline:
    """Tests for the refactored OCRPipeline using dependency injection."""

    def test_pipeline_process(self):
        img = Image.new("RGB", (100, 100), color=(255, 255, 255))
        pipeline = OCRPipeline(
            ocr_engine=MockOCREngine(),
            nlp_processor=MockNLPProcessor(),
            spelling_engine=MockSpellingEngine()
        )
        doc = pipeline.process(img)

        assert doc.raw_text == "Mock extracted text."
        assert doc.corrected_text == "Mock corrected text."
        assert doc.detected_language == settings.default_lang_code
