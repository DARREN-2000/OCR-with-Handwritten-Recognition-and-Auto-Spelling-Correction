"""
Web UI routes for the OCR Spelling Correction System.
"""

import base64
import io
import os
import structlog

from fastapi import APIRouter, Request, UploadFile, File, Form, HTTPException, Response
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, PlainTextResponse
from PIL import Image
import magic

from ocr_correction.pipeline import maybe_resize, ocr_pipeline
from ocr_correction.exceptions import InvalidImageError

logger = structlog.get_logger(__name__)

web_bp = APIRouter(tags=["web"])

# Setup templates directory
templates = Jinja2Templates(directory=os.path.join(os.path.dirname(__file__), "..", "templates"))


@web_bp.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the home / upload page."""
    return templates.TemplateResponse(request=request, name="index.html")


@web_bp.get("/about/", response_class=HTMLResponse)
async def about(request: Request):
    """Render the about page."""
    return templates.TemplateResponse(request=request, name="about.html")


@web_bp.post("/upload/", response_class=HTMLResponse)
async def upload(request: Request, imagefile: UploadFile = File(...)):
    """Handle image upload, run OCR pipeline, and display results."""
    try:
        if not imagefile:
            raise InvalidImageError("No image file provided.")

        raw_bytes = await imagefile.read()

        if not raw_bytes:
            raise InvalidImageError("Empty image file provided.")

        mime_type = magic.from_buffer(raw_bytes, mime=True)
        if not mime_type.startswith("image/"):
            raise InvalidImageError(f"Unsupported file type: {mime_type}. Must be an image.")

        try:
            pil_img = Image.open(io.BytesIO(raw_bytes))
            pil_img.verify()

            pil_img = Image.open(io.BytesIO(raw_bytes))
        except Exception as e:
            raise InvalidImageError("Unsupported or corrupted file type") from e
        pil_img = maybe_resize(pil_img, raw_bytes)

        ext = (
            imagefile.filename.rsplit(".", 1)[1]
            if imagefile.filename and "." in imagefile.filename
            else "jpeg"
        )

        doc = ocr_pipeline(pil_img)

        img_b64 = (
            "data:image/" + ext + ";base64,"
            + base64.b64encode(raw_bytes).decode("utf-8")
        )
        return templates.TemplateResponse(request=request, name="result.html", context={"var": doc.corrected_text, "img": img_b64})

    except InvalidImageError as exc:
        logger.warning("Invalid image upload", error=str(exc))
        response = templates.TemplateResponse(request=request, name="error.html", context={"error": str(exc)})
        response.status_code = 400
        return response
    except Exception as exc:
        logger.exception("Upload processing failed", error=str(exc))
        response = templates.TemplateResponse(request=request, name="error.html", context={"error": "An internal error occurred."})
        response.status_code = 500
        return response


@web_bp.post("/gettext")
async def gettext(text_content: str = Form("")):
    """Download the corrected output as a text file."""
    headers = {
        "Content-Disposition": "attachment; filename=corrected_output.txt"
    }
    return PlainTextResponse(content=text_content, headers=headers)
