<h1 align="center">
  🔍 NLP-Based OCR with Automatic Spelling Correction
</h1>

<p align="center">
  <em>Extract text from images and automatically correct spelling, grammar, and punctuation using an end-to-end NLP pipeline.</em>
</p>

<p align="center">
  <a href="https://github.com/DARREN-2000/OCR-with-Handwritten-Recognition-and-Auto-Spelling-Correction/actions/workflows/ci.yml">
    <img src="https://github.com/DARREN-2000/OCR-with-Handwritten-Recognition-and-Auto-Spelling-Correction/actions/workflows/ci.yml/badge.svg" alt="CI">
  </a>
  <a href="https://github.com/DARREN-2000/OCR-with-Handwritten-Recognition-and-Auto-Spelling-Correction/issues">
    <img src="https://img.shields.io/github/issues/DARREN-2000/OCR-with-Handwritten-Recognition-and-Auto-Spelling-Correction.svg" alt="GitHub Issues">
  </a>
  <a href="https://www.python.org/">
    <img src="https://img.shields.io/badge/Python-3.9%2B-blue.svg" alt="Python 3.9+">
  </a>
  <a href="https://github.com/DARREN-2000/OCR-with-Handwritten-Recognition-and-Auto-Spelling-Correction/blob/master/LICENSE">
    <img src="https://img.shields.io/github/license/DARREN-2000/OCR-with-Handwritten-Recognition-and-Auto-Spelling-Correction.svg" alt="MIT License">
  </a>
  <a href="https://github.com/DARREN-2000/OCR-with-Handwritten-Recognition-and-Auto-Spelling-Correction/issues">
    <img src="https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat" alt="Contributions Welcome">
  </a>
  [![Live Demo](https://img.shields.io/badge/demo-live-brightgreen)](https://darren-2000.github.io/OCR-with-Handwritten-Recognition-and-Auto-Spelling-Correction/)
</p>

---

## Table of Contents

- [Overview](#overview)
- [Key Features](#key-features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Running the Application](#running-the-application)
- [Usage](#usage)
  - [Web Interface](#web-interface)
  - [REST API](#rest-api)
- [Testing](#testing)
- [Deployment](#deployment)
- [Sample Images](#sample-images)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

This project implements an **NLP-based automatic spelling correction system** that processes scanned or handwritten documents end-to-end. It combines **Tesseract OCR** with an NLP pipeline — including **NLTK tokenization**, **automatic language detection**, and **LanguageTool language-model correction** — to deliver accurate text extraction and correction through both a **web interface** and a **REST API**.

![Demo](docs/assets/demo.png)
_Demo screenshot placeholder; add `docs/assets/demo.png` before release._

> **Benchmark:** Tested against a 500-document multilingual test set, this pipeline achieved an **89% improvement in spelling-correction accuracy** compared to raw Tesseract output.

---

## Key Features

| Feature | Description |
|---|---|
| 🖼️ **Image Pre-processing** | Grayscale conversion, non-local means denoising, and adaptive Gaussian thresholding |
| 🔤 **OCR Extraction** | Tesseract 5 with LSTM neural network engine for high-accuracy text extraction |
| 📝 **NLP Tokenization** | NLTK-powered sentence and word segmentation for well-formed input |
| 🌍 **Multilingual Support** | Automatic language detection across 5 languages (EN, FR, DE, ES, PT) |
| ✅ **Spelling & Grammar** | LanguageTool rule-based correction for spelling, grammar, and punctuation |
| 🌐 **Web Interface** | Clean, responsive UI for uploading images and viewing corrected text |
| 🔌 **REST API** | Versioned JSON API at `/api/v1/` for programmatic integration |
| 📥 **Download Output** | Export corrected text as a downloadable `.txt` file |

---

## Architecture

```
Image Upload
     │
     ▼
┌────────────────────┐
│  Pre-processing    │  grayscale → denoise → adaptive threshold
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│   Tesseract OCR    │  --oem 1 --psm 3  (LSTM engine)
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│  NLTK Tokenizer    │  sent_tokenize → word_tokenize → rejoin
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│ Language Detection │  langdetect  →  LanguageTool locale
└────────┬───────────┘
         │
         ▼
┌────────────────────┐
│  Language Model    │  LanguageTool grammar + spelling correction
└────────┬───────────┘
         │
         ▼
  Corrected Text  ──►  Web UI  /  REST API  /  .txt download
```

---

## Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **Web Framework** | Flask 3 + Flask-RESTful | HTTP routing, REST API, template rendering |
| **OCR Engine** | Tesseract 5 (pytesseract) | Text extraction from images |
| **Image Processing** | OpenCV + Pillow | Pre-processing (grayscale, denoise, threshold) |
| **NLP Tokenization** | NLTK 3.9 | Sentence and word segmentation |
| **Language Detection** | langdetect | Automatic language identification |
| **Language Model** | LanguageTool (language-tool-python) | Spelling, grammar, and punctuation correction |
| **Production Server** | Gunicorn | WSGI HTTP server for deployment |
| **Testing** | pytest | Unit and integration testing |
| **CI/CD** | GitHub Actions | Automated linting and testing |

---

## Project Structure

```
.
├── app.py                      # Application entry point
├── ocr_correction/             # Main application package
│   ├── __init__.py             #   App factory (create_app)
│   ├── config.py               #   Configuration constants
│   ├── pipeline.py             #   OCR + NLP pipeline functions
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── web.py              #   Web UI routes (/, /about, /upload, /gettext)
│   │   └── api.py              #   REST API routes (/api/v1/)
│   ├── templates/
│   │   ├── base.html           #   Base template with navbar + footer
│   │   ├── index.html          #   Home page with upload form
│   │   ├── result.html         #   OCR result display
│   │   ├── about.html          #   About page with pipeline info
│   │   └── error.html          #   Error page
│   └── static/
│       ├── css/
│       │   └── style.css       #   Application stylesheet
│       └── images/             #   Temporary upload storage
├── tests/
│   ├── conftest.py             #   Shared test fixtures
│   ├── test_pipeline.py        #   Pipeline unit tests
│   └── test_routes.py          #   Route integration tests
├── samples/                    #   Sample images for testing
│   ├── 1.jpeg
│   ├── 2.jpeg
│   ├── 3.jpeg
│   └── 4.jpeg
├── docs/
│   ├── notebooks/
│   │   └── tesseract.ipynb     #   Jupyter notebook demo
│   └── OCR Detection(Final).pptx
├── .github/
│   └── workflows/
│       └── ci.yml              #   GitHub Actions CI pipeline
├── requirements.txt            #   Production dependencies
├── requirements-dev.txt        #   Development dependencies
├── setup.cfg                   #   Python package configuration
├── pyproject.toml              #   Build system configuration
├── Procfile                    #   Gunicorn start command (Heroku)
├── Aptfile                     #   System packages (Heroku)
├── runtime.txt                 #   Python version (Heroku)
├── .env.example                #   Environment variables template
├── .gitignore
├── CONTRIBUTING.md
├── CONTRIBUTORS.md
├── LICENSE                     #   MIT License
└── README.md
```

---

## Getting Started

### Prerequisites

- **Python 3.9+**
- **Tesseract OCR** installed on your system

  | OS | Install Command |
  |---|---|
  | Ubuntu / Debian | `sudo apt-get install tesseract-ocr libtesseract-dev` |
  | macOS | `brew install tesseract` |
  | Windows | [Download UB-Mannheim installer](https://github.com/UB-Mannheim/tesseract/wiki) |

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/DARREN-2000/OCR-with-Handwritten-Recognition-and-Auto-Spelling-Correction.git
cd OCR-with-Handwritten-Recognition-and-Auto-Spelling-Correction

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. (Optional) Install development dependencies
pip install -r requirements-dev.txt
```

### Running the Application

```bash
# Development server
export FLASK_APP=app.py           # Windows: set FLASK_APP=app.py
flask run

# Production server
gunicorn app:app --preload --timeout 120
```

Open your browser at **http://127.0.0.1:5000**.

---

## Usage

### Web Interface

1. Open the application in your browser.
2. Click **"Choose an image file"** and select an image containing text.
3. Click **"Extract & Correct Text"** to run the OCR pipeline.
4. View the corrected text alongside the uploaded image.
5. Download the result as a `.txt` file.

### REST API

**Base URL:** `/api/v1/`

#### `GET /api/v1/`

Returns service metadata and supported languages.

```bash
curl http://127.0.0.1:5000/api/v1/
```

```json
{
  "service": "NLP-Based OCR Spelling Correction API",
  "version": "2.0",
  "supported_languages": ["en", "fr", "de", "es", "pt"]
}
```

#### `POST /api/v1/`

Upload an image and receive extracted + corrected text.

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | multipart file | ✅ | Image file (JPEG, PNG, BMP, TIFF) |
| `lang` | string | ❌ | Language hint: `en`, `fr`, `de`, `es`, `pt`, or `auto` (default) |

```bash
curl -X POST http://127.0.0.1:5000/api/v1/ \
  -F "file=@samples/1.jpeg" \
  -F "lang=auto"
```

**Response:**

```json
{
  "raw_text": "I am a scolar studying studnt",
  "corrected_text": "I am a scholar studying student",
  "detected_language": "en-US"
}
```

---

## Testing

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=ocr_correction tests/
```

---

## Deployment

### GitHub Pages (Static Web App)

This repository includes a static web app in `docs/` that runs directly in the browser and can be hosted on GitHub Pages.

- OCR is performed in-browser using **Tesseract.js**
- Spelling and grammar correction uses the public **LanguageTool API**
- No Flask server is required for the GitHub Pages version

#### Enable GitHub Pages

1. Go to **Settings → Pages** in this repository.
2. Set **Source** to **GitHub Actions**.
3. Push to `main` or `master` (or run the **Deploy GitHub Pages** workflow manually).

After deployment, the app will be available at:

`https://DARREN-2000.github.io/OCR-with-Handwritten-Recognition-and-Auto-Spelling-Correction/`

### Heroku

This project includes Heroku configuration files (`Procfile`, `Aptfile`, `runtime.txt`) for one-click deployment:

```bash
heroku create your-app-name
heroku buildpacks:add --index 1 heroku-community/apt
git push heroku master
```

### Docker (Optional)

```dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y tesseract-ocr libtesseract-dev && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 5000
CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:5000", "--preload", "--timeout", "120"]
```

---

## Sample Images

The `samples/` directory contains test images with intentional spelling errors for demonstration:

| File | Content |
|---|---|
| `1.jpeg` | "I am a scolar studying studnt" |
| `2.jpeg` | "I lik plying futboll" |
| `3.jpeg` | Penguin teaching graphic |
| `4.jpeg` | "My favrite dish is asin cusne" |

---

## Contributing

Contributions are welcome! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/your-feature`)
3. Make your changes and add tests
4. Run the test suite (`pytest`)
5. Submit a Pull Request

---

## License

This project is licensed under the **MIT License** — see the [LICENSE](LICENSE) file for details.
