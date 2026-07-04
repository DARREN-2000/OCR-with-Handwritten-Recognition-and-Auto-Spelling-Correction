import os
import functools
import structlog

import nltk
import pytesseract
from pytesseract.pytesseract import TesseractNotFoundError
import language_tool_python
from langdetect import LangDetectException, detect
from nltk.tokenize import sent_tokenize, word_tokenize
from PIL import Image

from ocr_correction.ports import BaseOCREngine, BaseNLPProcessor, BaseSpellingEngine
from ocr_correction.config import settings
from ocr_correction.exceptions import EngineError, LanguageDetectionError
from ocr_correction.domain import TextSnippet, BoundingBox

logger = structlog.get_logger(__name__)

# Pre-load NLTK data
for _resource in ("tokenizers/punkt", "tokenizers/punkt_tab"):
    try:
        nltk.data.find(_resource)
    except LookupError:
        nltk.download(_resource.split("/")[-1], quiet=True)

if settings.tesseract_cmd and os.path.exists(settings.tesseract_cmd):
    pytesseract.pytesseract.tesseract_cmd = settings.tesseract_cmd


class PaddleOCRAdapter(BaseOCREngine):
    """Adapter for PaddleOCR."""

    def __init__(self):
        try:
            from paddleocr import PaddleOCR
            # Initialize PaddleOCR model lazily. We'll disable logging to avoid clutter.
            self.model = PaddleOCR(use_angle_cls=True, lang='en', show_log=False)
        except ImportError as exc:
            logger.error("PaddleOCR is not installed.")
            raise EngineError("PaddleOCR is not installed. Please install it via pip.") from exc

    def extract_text(self, image: Image.Image) -> tuple[str, list[TextSnippet]]:
        import numpy as np
        try:
            # PaddleOCR expects a numpy array (cv2 image)
            img_array = np.array(image.convert('RGB'))

            result = self.model.ocr(img_array, cls=True)

            if not result or not result[0]:
                return "", []

            snippets = []
            full_text_parts = []

            # PaddleOCR returns a list of lines, each containing a list of bounding boxes and text/confidence
            # result[0] is the list of results for the first image (since we only pass one)
            for line in result[0]:
                # line format: [[p1, p2, p3, p4], (text, confidence)]
                box = line[0]
                text = line[1][0]
                confidence = float(line[1][1])

                # Calculate bounding box (x, y, w, h) from 4 points
                x_coords = [p[0] for p in box]
                y_coords = [p[1] for p in box]

                x_min, x_max = min(x_coords), max(x_coords)
                y_min, y_max = min(y_coords), max(y_coords)

                snippets.append(TextSnippet(
                    text=text,
                    confidence=confidence,
                    bounding_box=BoundingBox(
                        x=int(x_min),
                        y=int(y_min),
                        w=int(x_max - x_min),
                        h=int(y_max - y_min)
                    )
                ))
                full_text_parts.append(text)

            return "\n".join(full_text_parts), snippets
        except Exception as exc:
            raise EngineError(f"PaddleOCR extraction failed: {exc}") from exc


class TrOCRAdapter(BaseOCREngine):
    """Adapter for Transformer-based OCR (TrOCR) using HuggingFace."""

    def __init__(self):
        try:
            from transformers import TrOCRProcessor, VisionEncoderDecoderModel
            # Load pre-trained models. For handwritten text, microsoft/trocr-base-handwritten is often used.
            # Using a smaller model here or allowing it to be configurable would be better for a real app.
            logger.info("Initializing TrOCR model...")
            self.processor = TrOCRProcessor.from_pretrained("microsoft/trocr-base-handwritten")
            self.model = VisionEncoderDecoderModel.from_pretrained("microsoft/trocr-base-handwritten")
        except ImportError as exc:
            logger.error("transformers or torch is not installed.")
            raise EngineError("transformers and torch are required for TrOCR.") from exc

    def extract_text(self, image: Image.Image) -> tuple[str, list[TextSnippet]]:
        try:
            # Ensure image is RGB
            img_rgb = image.convert('RGB')

            # TrOCR doesn't natively return bounding boxes per word easily without complex attention mapping,
            # so we'll just process the whole image as a single snippet for now, or assume it's a line.
            # For a production system, a text detector (like CRAFT or DBNet) would precede TrOCR.
            pixel_values = self.processor(img_rgb, return_tensors="pt").pixel_values
            generated_ids = self.model.generate(pixel_values)
            generated_text = self.processor.batch_decode(generated_ids, skip_special_tokens=True)[0]

            # Return single snippet for the whole image since we lack bounding boxes
            snippets = [TextSnippet(
                text=generated_text,
                confidence=None,
                bounding_box=BoundingBox(x=0, y=0, w=img_rgb.width, h=img_rgb.height)
            )]

            return generated_text, snippets
        except Exception as exc:
            raise EngineError(f"TrOCR extraction failed: {exc}") from exc


class TesseractAdapter(BaseOCREngine):
    """Adapter for Tesseract OCR."""

    def extract_text(self, image: Image.Image) -> tuple[str, list[TextSnippet]]:
        try:
            full_text = pytesseract.image_to_string(image, config=settings.ocr_config)

            data = pytesseract.image_to_data(image, config=settings.ocr_config, output_type=pytesseract.Output.DICT)
            snippets = []
            for i in range(len(data['text'])):
                text = data['text'][i].strip()
                if not text:
                    continue
                try:
                    conf = float(data['conf'][i])
                except (ValueError, TypeError):
                    conf = None

                snippets.append(TextSnippet(
                    text=text,
                    confidence=conf,
                    bounding_box=BoundingBox(
                        x=int(data['left'][i]),
                        y=int(data['top'][i]),
                        w=int(data['width'][i]),
                        h=int(data['height'][i])
                    )
                ))

            return full_text, snippets
        except TesseractNotFoundError as exc:
            logger.error("Tesseract binary not found.")
            raise EngineError("Tesseract OCR is not installed or not in PATH.") from exc
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
