"""
NLP-Based OCR Spelling Correction System
-----------------------------------------
Flask application factory with modular OCR pipeline.
"""

import os

from flask import Flask

__version__ = "2.0.0"


def create_app(config_overrides=None):
    """Application factory for the OCR Spelling Correction System."""
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
    )

    # Default configuration
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024  # 16 MB upload limit
    app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "dev-secret-key")

    if config_overrides:
        app.config.update(config_overrides)

    # Register blueprints
    from ocr_correction.routes.web import web_bp
    from ocr_correction.routes.api import api_bp

    app.register_blueprint(web_bp)
    app.register_blueprint(api_bp)

    return app
