"""
NLP-Based OCR Spelling Correction System
-----------------------------------------
Application entry point.

This module creates the Flask application using the factory pattern
defined in the ``ocr_correction`` package.

Usage:
    flask run                       # Development server
    gunicorn app:app --preload      # Production (Gunicorn)
"""

from ocr_correction import create_app
import structlog
import sys
import os

# Add src/ to the path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'src')))


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
    app.run(debug=False)
