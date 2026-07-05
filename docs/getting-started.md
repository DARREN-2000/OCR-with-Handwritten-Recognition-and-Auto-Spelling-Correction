# Getting Started

This guide will walk you through setting up the High-Fidelity OCR & NLP Correction Pipeline locally.

## Prerequisites

Before you begin, ensure you have the following installed:

1. **Python 3.9+**
2. **Docker** and **Docker Compose** (Recommended for the easiest setup)
3. **Tesseract OCR** (Required if running manually without Docker)

### Installing Tesseract
If you are running the application outside of Docker, you must install Tesseract on your host machine.

*   **Ubuntu / Debian:**
    ```bash
    sudo apt-get update
    sudo apt-get install -y tesseract-ocr libtesseract-dev
    ```
*   **macOS:**
    ```bash
    brew install tesseract
    ```
*   **Windows:**
    Download the installer from [UB-Mannheim](https://github.com/UB-Mannheim/tesseract/wiki). Ensure the installation path is added to your system's `PATH`.

---

## Method 1: Using Docker (Recommended)

The project includes a `docker-compose.yml` file that orchestrates the FastAPI application, the Celery worker, and a Redis message broker.

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/DARREN-2000/OCR-with-Handwritten-Recognition-and-Auto-Spelling-Correction.git
    cd OCR-with-Handwritten-Recognition-and-Auto-Spelling-Correction
    ```

2.  **Start the stack:**
    ```bash
    docker-compose up --build
    ```
    *This will pull the necessary images, build the application containers, and start all services.*

3.  **Access the API:**
    Open your browser and navigate to the interactive Swagger documentation:
    [http://localhost:8000/docs](http://localhost:8000/docs)

---

## Method 2: Manual Installation

If you prefer to run the services directly on your host machine for development:

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/DARREN-2000/OCR-with-Handwritten-Recognition-and-Auto-Spelling-Correction.git
    cd OCR-with-Handwritten-Recognition-and-Auto-Spelling-Correction
    ```

2.  **Create and activate a virtual environment:**
    ```bash
    python3 -m venv venv
    source venv/bin/activate  # On Windows: venv\Scripts\activate
    ```

3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Start Redis:**
    You must have a Redis server running locally.
    ```bash
    redis-server &
    ```

5.  **Start the Celery Worker:**
    The Celery worker handles the heavy OCR and NLP tasks.
    ```bash
    celery -A worker.celery_app worker --loglevel=info &
    ```

6.  **Start the FastAPI Application:**
    ```bash
    uvicorn app:app --reload
    ```

7.  **Access the API:**
    Open [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs) in your browser.

---

## Verifying the Installation

You can test the API using `curl`. We provide sample images in the `samples/` directory.

**1. Submit an Image:**
```bash
curl -X POST "http://localhost:8000/api/v1/async" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@samples/1.jpeg"
```

You will receive a `task_id` in response.

**2. Check the Result:**
Using the `task_id` from the previous step, poll the status endpoint:
```bash
curl -X GET "http://localhost:8000/api/v1/tasks/<YOUR_TASK_ID>"
```
When the status is `"SUCCESS"`, you will see the extracted and corrected text.
