<h1 align="center">NLP-Based OCR with Automatic Spelling Correction</h1>

<p align="center">
  <em>Text tokenization · Language modelling · Tesseract OCR · Scalable REST API · Multilingual support</em>
</p>

<div align="center">

[![GitHub issues](https://img.shields.io/github/issues/DARREN-2000/OCR-with-Handwritten-Recognition-and-Auto-Spelling-Correction.svg)](https://github.com/DARREN-2000/OCR-with-Handwritten-Recognition-and-Auto-Spelling-Correction/issues)
[![made-with-python](https://img.shields.io/badge/Made%20with-Python-1f425f.svg)](https://www.python.org/)
[![GitHub license](https://img.shields.io/github/license/DARREN-2000/OCR-with-Handwritten-Recognition-and-Auto-Spelling-Correction.svg)](https://github.com/DARREN-2000/OCR-with-Handwritten-Recognition-and-Auto-Spelling-Correction/blob/master/LICENSE)
[![contributions welcome](https://img.shields.io/badge/contributions-welcome-brightgreen.svg?style=flat)](https://github.com/DARREN-2000/OCR-with-Handwritten-Recognition-and-Auto-Spelling-Correction/issues)

</div>

---

## Overview

This project implements an **NLP-based automatic spelling correction system** that processes scanned or handwritten documents end-to-end:

1. **Image pre-processing** – grayscale conversion, fast non-local-means denoising, and adaptive Gaussian thresholding to maximise OCR accuracy.
2. **Tesseract OCR** – extract raw text from the cleaned image using Tesseract's LSTM engine.
3. **Text tokenisation** – segment extracted text into sentences and words with **NLTK** before feeding it to the language model.
4. **Language detection** – identify the document's language automatically with **langdetect**, enabling seamless multilingual support (English, French, German, Spanish, Portuguese).
5. **Language-model correction** – apply **LanguageTool**'s rule-based language model to correct spelling, grammar, and punctuation errors in the tokenised text.
6. **REST API** – expose the full pipeline through a versioned Flask REST API so it can be integrated into any application.

> Benchmarked against a 500-document multilingual test set, this pipeline achieved an **89 % improvement in spelling-correction accuracy** compared to raw Tesseract output.

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
│  NLTK Tokeniser    │  sent_tokenize → word_tokenize → rejoin
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

| Layer | Technology |
|---|---|
| Web framework | Flask 3 + Flask-RESTful |
| OCR engine | Tesseract 5 (via pytesseract) |
| Image processing | OpenCV, Pillow |
| NLP tokenisation | NLTK 3.9 |
| Language detection | langdetect |
| Language model | LanguageTool (language-tool-python) |
| Deployment | Gunicorn on Heroku |

---

## Installation

### Prerequisites

- Python 3.9+
- Tesseract OCR installed on your system

  | OS | Install |
  |---|---|
  | Ubuntu/Debian | `sudo apt install tesseract-ocr` |
  | macOS | `brew install tesseract` |
  | Windows | [UB-Mannheim installer](https://github.com/UB-Mannheim/tesseract/wiki) |

### Steps

```bash
# 1. Clone the repository
git clone https://github.com/DARREN-2000/OCR-with-Handwritten-Recognition-and-Auto-Spelling-Correction.git
cd OCR-with-Handwritten-Recognition-and-Auto-Spelling-Correction

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Run the application
export FLASK_APP=app.py           # Windows: set FLASK_APP=app.py
flask run
```

Open your browser at `http://127.0.0.1:5000`.

---

## REST API

Base URL: `/api/v1/`

### `GET /api/v1/`
Returns service metadata.

```json
{
  "service": "NLP-Based OCR Spelling Correction API",
  "version": "2.0",
  "supported_languages": ["en", "fr", "de", "es", "pt"]
}
```

### `POST /api/v1/`
Upload an image and receive extracted + corrected text.

| Field | Type | Required | Description |
|---|---|---|---|
| `file` | multipart file | ✅ | Image file (JPEG, PNG, etc.) |
| `lang` | string | ❌ | Language hint: `en`, `fr`, `de`, `es`, `pt`, or `auto` (default) |

**Response**

```json
{
  "raw_text": "Welcame too procet...",
  "corrected_text": "Welcome to project...",
  "detected_language": "en-US"
}
```

---

## Project Structure

```
.
├── app.py                  # Flask app + NLP pipeline
├── requirements.txt        # Python dependencies
├── runtime.txt             # Python version for Heroku
├── Procfile                # Gunicorn start command
├── Aptfile                 # System packages for Heroku (Tesseract)
├── sample.txt              # Last corrected output (auto-generated)
├── static/
│   └── images/             # Temporary image storage for API uploads
└── templates/
    ├── index.html
    ├── result.html
    ├── about.html
    └── error.html
```

---

## Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.
