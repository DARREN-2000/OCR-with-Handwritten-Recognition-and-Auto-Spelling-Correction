# Contributing to OCR-with-Handwritten-Recognition-and-Auto-Spelling-Correction

First off, thank you for considering contributing to this project! It's people like you that make open-source software such a great community.

## 1. Where do I go from here?

If you've noticed a bug or have a feature request, make sure to check our [Issues](https://github.com/DARREN-2000/OCR-with-Handwritten-Recognition-and-Auto-Spelling-Correction/issues) first to see if someone else has already created one. If not, go ahead and make one!

## 2. Fork & create a branch

If this is something you think you can fix, then fork the repository and create a branch with a descriptive name.

## 3. Implement your fix or feature

Make sure your code adheres to our architectural guidelines:
*   We use **Hexagonal Architecture** (Ports and Adapters) in `src/ocr_correction`. Ensure your business logic does not leak into the API or Worker layers.
*   We use **FastAPI** for our API.
*   We use **Celery** for asynchronous task execution.

## 4. Run the tests

Before submitting your pull request, please make sure all tests pass.

```bash
export PYTHONPATH=src:$PYTHONPATH
python -m pytest tests/
```

## 5. Make a Pull Request

Submit a pull request with a clear title and description. We will review it as soon as possible.
