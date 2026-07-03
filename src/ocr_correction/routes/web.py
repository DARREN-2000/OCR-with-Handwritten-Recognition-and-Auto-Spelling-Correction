"""
Web UI routes for the OCR Spelling Correction System.
"""

import base64
import io
import structlog

from flask import Blueprint, Response, render_template, request
from PIL import Image

from ocr_correction.pipeline import maybe_resize, ocr_pipeline
from ocr_correction.exceptions import InvalidImageError

logger = structlog.get_logger(__name__)

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
        if "imagefile" not in request.files:
            raise InvalidImageError("No image file provided.")

        imagefile = request.files["imagefile"]
        raw_bytes = imagefile.read()

        if not raw_bytes:
            raise InvalidImageError("Empty image file provided.")

        try:
            pil_img = Image.open(io.BytesIO(raw_bytes))
            pil_img.verify()

            pil_img = Image.open(io.BytesIO(raw_bytes))
        except Exception as e:
            raise InvalidImageError("Unsupported or corrupted file type") from e
        pil_img = maybe_resize(pil_img, raw_bytes)

        ext = (
            imagefile.filename.rsplit(".", 1)[1]
            if "." in imagefile.filename
            else "jpeg"
        )

        doc = ocr_pipeline(pil_img)

        img_b64 = (
            "data:image/" + ext + ";base64,"
            + base64.b64encode(raw_bytes).decode("utf-8")
        )
        return render_template("result.html", var=doc.corrected_text, img=img_b64)

    except InvalidImageError as exc:
        logger.warning("Invalid image upload", error=str(exc))
        return render_template("error.html", error=str(exc)), 400
    except Exception as exc:
        logger.exception("Upload processing failed", error=str(exc))
        return render_template("error.html", error="An internal error occurred."), 500


@web_bp.route("/gettext", methods=["POST"])
def gettext():
    """Download the corrected output as a text file."""
    src = request.form.get("text_content", "")
    return Response(
        src,
        mimetype="text/plain",
        headers={
            "Content-Disposition": "attachment; filename=corrected_output.txt"
        },
    )
