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

import logging

from ocr_correction import create_app

# Logging setup for the application
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
)

app = create_app()

if __name__ == "__main__":
    app.run(debug=False)
