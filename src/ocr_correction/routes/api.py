"""
REST API routes for the OCR Spelling Correction System.
"""

import structlog
import io
import uuid
import magic
from typing import Dict, Any

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, BackgroundTasks, status
from PIL import Image

from ocr_correction.config import LANGUAGE_MAP
from ocr_correction.pipeline import ocr_pipeline
from ocr_correction.exceptions import InvalidImageError

logger = structlog.get_logger(__name__)

api_bp = APIRouter(prefix="/api/v1", tags=["api"])

# In-memory store for task results (in a real app, use Redis/DB)
_tasks: Dict[str, Dict[str, Any]] = {}

def process_ocr_task(task_id: str, raw_bytes: bytes, lang_hint: str):
    _tasks[task_id] = {"status": "processing"}
    try:
        pil_img = Image.open(io.BytesIO(raw_bytes))
        # No need to verify again, we did it in the endpoint
        doc = ocr_pipeline(pil_img, lang_hint)
        _tasks[task_id] = {
            "status": "completed",
            "result": {
                "raw_text": doc.raw_text,
                "corrected_text": doc.corrected_text,
                "detected_language": doc.detected_language,
                "snippets": [s.model_dump() for s in doc.snippets]
            }
        }
    except Exception as exc:
        logger.exception("Background task processing error", error=str(exc))
        _tasks[task_id] = {
            "status": "failed",
            "error": "Processing failed due to an internal error."
        }

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
async def post_async(background_tasks: BackgroundTasks, file: UploadFile = File(...), lang: str = Form("auto")):
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

        task_id = str(uuid.uuid4())
        _tasks[task_id] = {"status": "pending"}

        background_tasks.add_task(process_ocr_task, task_id, raw_bytes, lang)

        return {"task_id": task_id, "status": "pending"}

    except InvalidImageError as exc:
        logger.warning("Invalid image upload via API", error=str(exc))
        raise HTTPException(status_code=400, detail={"error": "Invalid image", "detail": str(exc)})
    except Exception as exc:
        logger.exception("API processing error", error=str(exc))
        raise HTTPException(status_code=500, detail={"error": "Processing failed", "detail": "An internal error occurred."})

@api_bp.get("/tasks/{task_id}")
def get_task_status(task_id: str):
    """Poll task status."""
    if task_id not in _tasks:
        raise HTTPException(status_code=404, detail="Task not found")
    return _tasks[task_id]
