"""
NLP-Based OCR Spelling Correction System
-----------------------------------------
Application entry point.

This module creates the FastAPI application using the factory pattern
defined in the ``ocr_correction`` package.

Usage:
    uvicorn app:app --reload        # Development server
    uvicorn app:app --host 0.0.0.0  # Production
"""

import sys
import os
import uvicorn
import structlog

# Add src/ to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))

from ocr_correction import create_app

structlog.configure(
    processors=[
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.processors.JSONRenderer(),
    ],
    logger_factory=structlog.PrintLoggerFactory(),
)

app = create_app()

if __name__ == "__main__":
    uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=False)
