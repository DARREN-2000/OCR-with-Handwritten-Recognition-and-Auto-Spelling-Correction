"""Unit tests for the OCR pipeline functions."""

import numpy as np
from PIL import Image

from ocr_correction.config import DEFAULT_LANG_CODE, LANGUAGE_MAP
from ocr_correction.pipeline import (
    detect_language,
    maybe_resize,
    preprocess_image,
    tokenize,
)


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


class TestDetectLanguage:
    """Tests for the detect_language function."""

    def test_returns_string(self):
        result = detect_language("Hello world")
        assert isinstance(result, str)

    def test_fallback_on_empty(self):
        result = detect_language("")
        assert result == DEFAULT_LANG_CODE

    def test_returns_valid_lang_code(self):
        result = detect_language("This is a simple English sentence.")
        valid_codes = set(LANGUAGE_MAP.values()) | {DEFAULT_LANG_CODE}
        assert result in valid_codes


class TestTokenize:
    """Tests for the tokenize function."""

    def test_returns_string(self):
        result = tokenize("Hello world. How are you?")
        assert isinstance(result, str)

    def test_preserves_words(self):
        result = tokenize("Hello world")
        assert "Hello" in result
        assert "world" in result

    def test_handles_empty(self):
        result = tokenize("")
        assert isinstance(result, str)

    def test_multiple_sentences(self):
        text = "First sentence. Second sentence."
        result = tokenize(text)
        assert "First" in result
        assert "Second" in result
