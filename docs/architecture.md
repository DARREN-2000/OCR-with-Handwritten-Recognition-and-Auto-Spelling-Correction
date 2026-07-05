# Architecture Deep Dive

This document explains the internal architecture of the NLP-Based OCR Spelling Correction System. The system is designed for high throughput, maintainability, and extensibility.

## 1. High-Level Architecture

The system operates as an asynchronous, event-driven microservice. It is designed to decouple the fast HTTP request/response cycle from the slow, CPU-bound machine learning and image processing tasks.

```mermaid
graph LR
    Client(Client) -->|1. POST Image| API[FastAPI Gateway]
    API -->|2. HTTP 202, Task ID| Client
    API -->|3. Publish Task| Redis[(Redis Broker)]
    Worker[Celery Worker] -->|4. Consume Task| Redis
    Worker -->|5. Process Pipeline| Core[src/ocr_correction]
    Worker -->|6. Save Result| Redis
    Client -->|7. GET /status/{id}| API
    API -->|8. Read Result| Redis
    API -->|9. HTTP 200, Data| Client
```

### Components
*   **FastAPI Gateway (`app.py`):** Handles incoming HTTP requests, validates payloads using Pydantic, and enqueues tasks.
*   **Redis Broker:** Acts as the message queue for Celery tasks and the state store for task results.
*   **Celery Worker (`worker.py`):** A background process that executes the heavy computational OCR and NLP pipeline.
*   **Core Domain (`src/ocr_correction`):** The business logic, isolated using Hexagonal Architecture.

## 2. Hexagonal Architecture (Ports and Adapters)

The core logic located in `src/ocr_correction` follows **Domain-Driven Design (DDD)** and **Hexagonal Architecture**. This ensures that our business rules do not depend on external libraries (like OpenCV or Tesseract), making the system highly testable and extensible.

### The Domain (`domain.py`)
Defines the core entities, such as `Document` and `TextSnippet`. These are pure Python objects (implemented via Pydantic) that represent the state of the data as it flows through the system.

### Ports (`ports.py`)
Ports are abstract interfaces (`abc.ABC`). They define *what* needs to be done without specifying *how*.
*   `BaseOCREngine`: Interface for extracting text from an image.
*   `BaseNLPTokenizer`: Interface for splitting text into sentences/words.
*   `BaseSpellingCorrection`: Interface for correcting text.

### Adapters (`adapters.py`)
Adapters are the concrete implementations of the Ports. They integrate third-party libraries.
*   `TesseractAdapter`: Implements `BaseOCREngine` using `pytesseract`.
*   `NLTKProcessor`: Implements `BaseNLPTokenizer` using `nltk`.
*   `LanguageToolAdapter`: Implements `BaseSpellingCorrection` using `language_tool_python`.

Because of this design, if we want to upgrade from Tesseract to TrOCR, we simply write a `TrOCRAdapter` that implements `BaseOCREngine` and inject it into the pipeline. The core business logic remains untouched.

## 3. The Processing Pipeline (`pipeline.py`)

When a Celery worker picks up a task, it executes the `ocr_pipeline`.

1.  **Image Pre-processing:** The raw image bytes are processed using OpenCV (grayscale, non-local means denoising, adaptive thresholding) to improve OCR accuracy.
2.  **OCR Extraction:** The pre-processed image is passed to the OCR Adapter (Tesseract) to extract raw text.
3.  **NLP Tokenization:** The raw text is passed to the NLP Adapter (NLTK) to be logically chunked into sentences.
4.  **Language Detection & Correction:** The language is detected, and the text is passed to the Correction Adapter (LanguageTool) to fix spelling and grammar.
5.  **Result Compilation:** The final corrected text is structured into a `Document` domain object and returned.

## 4. Error Handling & Logging

*   **Exceptions (`exceptions.py`):** Custom domain exceptions (e.g., `EngineError`, `ConfigurationError`) are used instead of generic Python exceptions. This allows the API to return meaningful HTTP status codes (e.g., 400 vs 500).
*   **Structured Logging:** The application uses `structlog` to output logs in JSON format. This is crucial for production environments, as it allows logs to be easily parsed and queried by systems like Datadog, ELK, or CloudWatch.