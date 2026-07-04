"""
REST API routes for the OCR Spelling Correction System.
"""

import structlog
import io
import magic
import base64

from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from PIL import Image

from celery.result import AsyncResult
from ocr_correction.worker import process_ocr_task
from ocr_correction.config import LANGUAGE_MAP
from ocr_correction.pipeline import ocr_pipeline
from ocr_correction.exceptions import InvalidImageError

logger = structlog.get_logger(__name__)

api_bp = APIRouter(prefix="/api/v1", tags=["api"])


@api_bp.get("/")
def get_info():
    """Service info."""
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
            "POST /api/v1/": "Upload image synchronously → corrected text",
            "POST /api/v1/async": "Upload image asynchronously → task ID",
            "GET  /api/v1/tasks/{task_id}": "Poll task status",
        },
    }


@api_bp.post("/")
async def post_sync(file: UploadFile = File(...), lang: str = Form("auto")):
    """Synchronous file upload."""
    if not file:
        raise HTTPException(status_code=400, detail="No image file provided")

    try:
        raw_bytes = await file.read()
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

        doc = ocr_pipeline(pil_img, lang)

        return {
            "raw_text": doc.raw_text,
            "corrected_text": doc.corrected_text,
            "detected_language": doc.detected_language,
            "snippets": [s.model_dump() for s in doc.snippets]
        }

    except InvalidImageError as exc:
        logger.warning("Invalid image upload via API", error=str(exc))
        raise HTTPException(status_code=400, detail={"error": "Invalid image", "detail": str(exc)})
    except Exception as exc:
        logger.exception("API processing error", error=str(exc))
        raise HTTPException(status_code=500, detail={"error": "Processing failed", "detail": "An internal error occurred."})


@api_bp.post("/async")
async def post_async(file: UploadFile = File(...), lang: str = Form("auto")):
    """Asynchronous file upload returning a task ID."""
    if not file:
        raise HTTPException(status_code=400, detail="No image file provided")

    try:
        raw_bytes = await file.read()
        if not raw_bytes:
            raise InvalidImageError("Empty image file provided.")

        mime_type = magic.from_buffer(raw_bytes, mime=True)
        if not mime_type.startswith("image/"):
            raise InvalidImageError(f"Unsupported file type: {mime_type}. Must be an image.")

        try:
            pil_img = Image.open(io.BytesIO(raw_bytes))
            pil_img.verify()
        except Exception as e:
            raise InvalidImageError("Unsupported or corrupted file type") from e

        # We must serialize the raw_bytes using base64 so Celery JSON serializer handles it.
        raw_bytes_b64 = base64.b64encode(raw_bytes).decode('utf-8')
        task = process_ocr_task.delay(raw_bytes_b64, lang)

        return {"task_id": task.id, "status": "pending"}

    except InvalidImageError as exc:
        logger.warning("Invalid image upload via API", error=str(exc))
        raise HTTPException(status_code=400, detail={"error": "Invalid image", "detail": str(exc)})
    except Exception as exc:
        logger.exception("API processing error", error=str(exc))
        raise HTTPException(status_code=500, detail={"error": "Processing failed", "detail": "An internal error occurred."})


@api_bp.get("/tasks/{task_id}")
def get_task_status(task_id: str):
    """Poll task status."""
    task = AsyncResult(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")

    if task.state == 'PENDING':
        return {"status": "pending"}
    elif task.state == 'SUCCESS':
        return task.result
    elif task.state == 'FAILURE':
        return {"status": "failed", "error": str(task.info)}
    else:
        return {"status": task.state.lower()}
