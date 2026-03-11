"""
Web UI routes for the OCR Spelling Correction System.
"""

import base64
import logging

from flask import Blueprint, Response, render_template, request
from PIL import Image

from ocr_correction.config import OUTPUT_FILE
from ocr_correction.pipeline import maybe_resize, ocr_pipeline

logger = logging.getLogger(__name__)

web_bp = Blueprint("web", __name__)


@web_bp.route("/")
def home():
    """Render the home / upload page."""
    return render_template("index.html")


@web_bp.route("/about/")
def about():
    """Render the about page."""
    return render_template("about.html")


@web_bp.route("/upload/", methods=["GET", "POST"])
def upload():
    """Handle image upload, run OCR pipeline, and display results."""
    try:
        imagefile = request.files.get("imagefile", "")
        raw_bytes = request.files["imagefile"].read()

        pil_img = Image.open(imagefile)
        pil_img = maybe_resize(pil_img, raw_bytes)

        ext = (
            imagefile.filename.rsplit(".", 1)[1]
            if "." in imagefile.filename
            else "jpeg"
        )

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


@web_bp.route("/gettext")
def gettext():
    """Download the last corrected output as a text file."""
    with open(OUTPUT_FILE, encoding="utf-8") as fh:
        src = fh.read()
    return Response(
        src,
        mimetype="text/plain",
        headers={
            "Content-Disposition": "attachment; filename=corrected_output.txt"
        },
    )
