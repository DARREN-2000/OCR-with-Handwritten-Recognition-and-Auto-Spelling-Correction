"""
NLP-Based OCR Spelling Correction System
-----------------------------------------
FastAPI application factory with modular OCR pipeline.
"""

import os

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

__version__ = "2.0.0"


def create_app(config_overrides=None):
    """Application factory for the OCR Spelling Correction System."""
    app = FastAPI(
        title="NLP-Based OCR Spelling Correction API",
        version=__version__,
        description="Scalable REST API for NLP-based OCR text extraction and spelling correction.",
    )

    # Mount static files
    app.mount(
        "/static",
        StaticFiles(directory=os.path.join(os.path.dirname(__file__), "static")),
        name="static"
    )

    # Register routers
    from ocr_correction.routes.web import web_bp
    from ocr_correction.routes.api import api_bp

    app.include_router(web_bp)
    app.include_router(api_bp)

    return app
