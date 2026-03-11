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

app = create_app()

if __name__ == "__main__":
    app.run(debug=False)
