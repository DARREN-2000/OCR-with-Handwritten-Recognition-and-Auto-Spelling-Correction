import os
from celery import Celery
import structlog
from PIL import Image
import io

from ocr_correction.pipeline import ocr_pipeline
from ocr_correction.exceptions import InvalidImageError

logger = structlog.get_logger(__name__)

# Use Redis URL from environment or default for local development
redis_url = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')

celery_app = Celery(
    'ocr_tasks',
    broker=redis_url,
    backend=redis_url
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
)

import base64

@celery_app.task(bind=True, name="ocr_tasks.process_image")
def process_ocr_task(self, raw_bytes_b64: str | bytes, lang_hint: str = "auto"):
    """
    Background task to process an OCR request.
    """
    logger.info("Starting background OCR task", task_id=self.request.id, lang_hint=lang_hint)
    try:
        if isinstance(raw_bytes_b64, str):
            raw_bytes = base64.b64decode(raw_bytes_b64)
        else:
            raw_bytes = raw_bytes_b64
        pil_img = Image.open(io.BytesIO(raw_bytes))
        doc = ocr_pipeline(pil_img, lang_hint)
        logger.info("Completed background OCR task", task_id=self.request.id)

        return {
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
        # Ensure we return a dictionary instead of raising an un-serializable exception back
        return {
            "status": "failed",
            "error": "Processing failed due to an internal error."
        }
