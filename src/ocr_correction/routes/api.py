"""
REST API routes for the OCR Spelling Correction System.
"""

import structlog
import io

import werkzeug
from flask import Blueprint
from flask_restful import Api, Resource, reqparse
from PIL import Image

from ocr_correction.config import LANGUAGE_MAP
from ocr_correction.pipeline import ocr_pipeline
from ocr_correction.exceptions import InvalidImageError

logger = structlog.get_logger(__name__)

api_bp = Blueprint("api", __name__)
api = Api(api_bp)

_parser = reqparse.RequestParser()
_parser.add_argument(
    "file", type=werkzeug.datastructures.FileStorage, location="files"
)
_parser.add_argument("lang", type=str, location="form", default="auto")


class OCRCorrectionAPI(Resource):
    """
    Scalable REST API for NLP-based OCR text extraction and spelling correction.

    GET  /api/v1/  – service info
    POST /api/v1/  – upload an image; returns raw OCR text and corrected text
                     Optional form field: lang  (en | fr | de | es | pt | auto)
    """

    def get(self):
        return {
            "service": "NLP-Based OCR Spelling Correction API",
            "version": "2.0",
            "description": (
                "Tesseract OCR combined with NLTK text tokenization and "
                "LanguageTool language-model correction for multilingual "
                "documents."
            ),
            "supported_languages": list(LANGUAGE_MAP.keys()),
            "endpoints": {
                "GET  /api/v1/": "Service info (this response)",
                "POST /api/v1/": "Upload image → corrected text",
            },
        }, 200

    def post(self):
        data = _parser.parse_args()
        if not data.get("file"):
            return {"error": "No image file provided"}, 400

        photo = data["file"]
        lang_hint = data.get("lang") or "auto"

        try:
            raw_bytes = photo.read()
            if not raw_bytes:
                raise InvalidImageError("Empty image file provided.")

            try:
                pil_img = Image.open(io.BytesIO(raw_bytes))
                pil_img.verify()  # Validate it's an actual image

                # Reopen since verify() can leave the file pointer at the end
                pil_img = Image.open(io.BytesIO(raw_bytes))
            except Exception as e:
                raise InvalidImageError("Unsupported or corrupted file type") from e
            raw_text, corrected_text, detected_lang = ocr_pipeline(
                pil_img, lang_hint
            )

            return {
                "raw_text": raw_text,
                "corrected_text": corrected_text,
                "detected_language": detected_lang,
            }, 200

        except InvalidImageError as exc:
            logger.warning("Invalid image upload via API", error=str(exc))
            return {"error": "Invalid image", "detail": str(exc)}, 400
        except Exception as exc:
            logger.exception("API processing error", error=str(exc))
            return {"error": "Processing failed", "detail": "An internal error occurred."}, 500


api.add_resource(OCRCorrectionAPI, "/api/v1/")
