"""
NLP-Based OCR Spelling Correction System
-----------------------------------------
Author : DARREN-2000
GitHub : https://github.com/DARREN-2000/OCR-with-Handwritten-Recognition-and-Auto-Spelling-Correction

Combines Tesseract OCR with an NLP pipeline (text tokenization + language
modeling via LanguageTool) to deliver automatic spelling correction for
multilingual documents through a scalable Flask REST API.
"""

import os
import sys
import base64
import logging
from math import floor

import cv2
import nltk
import numpy as np
import werkzeug
import language_tool_python
import pytesseract
from flask import Flask, Response, render_template, request
from flask_restful import Api, Resource, reqparse
from langdetect import LangDetectException, detect
from nltk.tokenize import sent_tokenize, word_tokenize
from PIL import Image

# ---------------------------------------------------------------------------
# NLTK data – download only when the resource is not already present
# ---------------------------------------------------------------------------
for _resource in ("tokenizers/punkt", "tokenizers/punkt_tab"):
    try:
        nltk.data.find(_resource)
    except LookupError:
        nltk.download(_resource.split("/")[-1], quiet=True)

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Tesseract path (Windows only – Linux/macOS find it on PATH automatically)
# ---------------------------------------------------------------------------
if sys.platform == "win32":
    _win_path = r"C:\Program Files\Tesseract-OCR\tesseract.exe"
    if os.path.exists(_win_path):
        pytesseract.pytesseract.tesseract_cmd = _win_path

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
IMAGE_SIZE_THRESHOLD_MB = 2
RESIZE_FACTOR = 0.9
OCR_CONFIG = "--oem 1 --psm 3"
OUTPUT_FILE = "sample.txt"

# Maps ISO-639-1 codes returned by langdetect → LanguageTool locale codes
LANGUAGE_MAP = {
    "en": "en-US",
    "fr": "fr",
    "de": "de-DE",
    "es": "es",
    "pt": "pt-PT",
}
DEFAULT_LANG_CODE = "en-US"

# ---------------------------------------------------------------------------
# Flask / Flask-RESTful setup
# ---------------------------------------------------------------------------
app = Flask(__name__)
api = Api(app)

_parser = reqparse.RequestParser()
_parser.add_argument("file", type=werkzeug.datastructures.FileStorage, location="files")
_parser.add_argument("lang", type=str, location="form", default="auto")


# ===========================================================================
# NLP Pipeline helpers
# ===========================================================================

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
        denoised, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY, 11, 2,
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


# ===========================================================================
# Web routes
# ===========================================================================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/about/")
def about():
    return render_template("about.html")


@app.route("/upload/", methods=["GET", "POST"])
def upload():
    try:
        imagefile = request.files.get("imagefile", "")
        raw_bytes = request.files["imagefile"].read()

        pil_img = Image.open(imagefile)
        pil_img = maybe_resize(pil_img, raw_bytes)

        ext = imagefile.filename.rsplit(".", 1)[1] if "." in imagefile.filename else "jpeg"

        _, corrected_text, _ = ocr_pipeline(pil_img)

        with open(OUTPUT_FILE, "w", encoding="utf-8") as fh:
            fh.write(corrected_text)

        img_b64 = (
            "data:image/" + ext + ";base64,"
            + base64.b64encode(raw_bytes).decode("utf-8")
        )
        return render_template("result.html", var=corrected_text, img=img_b64)

    except Exception as exc:
        logger.exception("Upload processing failed: %s", exc)
        return render_template("error.html")


@app.route("/gettext")
def gettext():
    with open(OUTPUT_FILE, encoding="utf-8") as fh:
        src = fh.read()
    return Response(
        src,
        mimetype="text/plain",
        headers={"Content-Disposition": "attachment; filename=corrected_output.txt"},
    )


# ===========================================================================
# REST API  –  /api/v1/
# ===========================================================================

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
                "LanguageTool language-model correction for multilingual documents."
            ),
            "supported_languages": list(LANGUAGE_MAP.keys()),
            "endpoints": {
                "GET  /api/v1/": "Service info (this response)",
                "POST /api/v1/": "Upload image → corrected text",
            },
        }, 200

    def post(self):
        data = _parser.parse_args()
        if not data["file"]:
            return {"error": "No image file provided"}, 400

        photo = data["file"]
        lang_hint = data.get("lang") or "auto"
        save_path = os.path.join("./static/images/", photo.filename)

        try:
            photo.save(save_path)
            pil_img = Image.open(save_path)
            raw_text, corrected_text, detected_lang = ocr_pipeline(pil_img, lang_hint)

            return {
                "raw_text": raw_text,
                "corrected_text": corrected_text,
                "detected_language": detected_lang,
            }, 200

        except Exception as exc:
            logger.exception("API processing error: %s", exc)
            return {"error": "Processing failed", "detail": str(exc)}, 500

        finally:
            if os.path.exists(save_path):
                os.remove(save_path)


api.add_resource(OCRCorrectionAPI, "/api/v1/")


if __name__ == "__main__":
    app.run(debug=False)

