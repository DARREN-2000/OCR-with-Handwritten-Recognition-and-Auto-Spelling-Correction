# API Reference

The backend exposes a RESTful API built with **FastAPI**.

For interactive documentation, start the server and navigate to `/docs` (Swagger UI) or `/redoc` (ReDoc).

## Base URL
All API routes are prefixed with `/api/v1`.

---

## 1. Extract Text from Image (Async)

Uploads an image for processing. Because the OCR and NLP pipeline is computationally expensive, this endpoint is asynchronous. It immediately returns a `task_id` that you use to poll for the final result.

**Endpoint:** `POST /api/v1/async`

### Request

*   **Content-Type:** `multipart/form-data`
*   **Body Parameters:**
    *   `file` (Required): The image file to process (JPEG, PNG).

**Example cURL:**
```bash
curl -X POST "http://localhost:8000/api/v1/async" \
  -H "accept: application/json" \
  -H "Content-Type: multipart/form-data" \
  -F "file=@samples/1.jpeg"
```

### Response

*   **Status Code:** `202 Accepted`
*   **Content-Type:** `application/json`

```json
{
  "task_id": "c9e2b143-6c7b-4a5f-9e2d-3a1b4c5d6e7f",
  "status": "PROCESSING"
}
```

---

## 2. Check Task Status

Retrieves the current status and (if complete) the result of an OCR extraction task.

**Endpoint:** `GET /api/v1/tasks/{task_id}`

### Request

*   **Path Parameters:**
    *   `task_id` (Required): The UUID returned by the `/async` endpoint.

**Example cURL:**
```bash
curl -X GET "http://localhost:8000/api/v1/tasks/c9e2b143-6c7b-4a5f-9e2d-3a1b4c5d6e7f"
```

### Responses

#### Pending / Processing
If the Celery worker is still processing the image:
*   **Status Code:** `200 OK`

```json
{
  "task_id": "c9e2b143-6c7b-4a5f-9e2d-3a1b4c5d6e7f",
  "status": "PROCESSING"
}
```

#### Success
If the pipeline completed successfully:
*   **Status Code:** `200 OK`

```json
{
  "status": "SUCCESS",
  "result": {
    "raw_text": "I am a scolar studying studnt",
    "corrected_text": "I am a scholar studying student",
    "language": "en",
    "confidence_score": 0.89
  }
}
```

#### Failure
If an error occurred during processing (e.g., the image was unreadable):
*   **Status Code:** `200 OK` (Note: The HTTP request to check status succeeded, but the underlying task failed).

```json
{
  "status": "FAILURE",
  "error": "Failed to parse image data. Ensure the file is a valid image."
}
```

#### Task Not Found
If the `task_id` does not exist in Redis (or has expired):
*   **Status Code:** `404 Not Found`

```json
{
  "detail": "Task not found"
}
```