"""Shared test fixtures for the OCR Spelling Correction test suite."""

import os
import pytest
from PIL import Image
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../src')))

from ocr_correction import create_app


@pytest.fixture
def app():
    """Create a FastAPI application configured for testing."""
    app = create_app(
        config_overrides={
            "TESTING": True,
            "SECRET_KEY": "test-secret",
        }
    )
    yield app


@pytest.fixture
def client(app):
    """Create a FastAPI test client."""
    from fastapi.testclient import TestClient
    return TestClient(app)


@pytest.fixture
def sample_image(tmp_path):
    """Create a simple test image with text-like content."""
    img = Image.new("RGB", (200, 50), color=(255, 255, 255))
    path = tmp_path / "test_image.png"
    img.save(str(path))
    return str(path)


@pytest.fixture
def sample_image_bytes(sample_image):
    """Return sample image as bytes."""
    with open(sample_image, "rb") as f:
        return f.read()


@pytest.fixture
def samples_dir():
    """Return the path to the samples directory."""
    return os.path.join(
        os.path.dirname(os.path.dirname(__file__)), "samples"
    )
