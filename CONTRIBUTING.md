# Contributing

Thank you for your interest in contributing to this project!

## Getting Started

1. **Fork** this repository and clone your fork locally.

   ```bash
   git clone https://github.com/{your-username}/OCR-with-Handwritten-Recognition-and-Auto-Spelling-Correction.git
   cd OCR-with-Handwritten-Recognition-and-Auto-Spelling-Correction
   ```

2. **Create a branch** for your change.

   ```bash
   git checkout -b feature/your-feature-name
   ```

3. **Set up the development environment.**

   ```bash
   python3 -m venv venv
   source venv/bin/activate   # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   pip install -r requirements-dev.txt
   ```

## Project Layout

| Directory | Purpose |
|---|---|
| `ocr_correction/` | Main application package (pipeline, routes, templates, static assets) |
| `tests/` | Unit and integration tests |
| `samples/` | Sample images for testing |
| `docs/` | Documentation, notebooks, and presentations |

## Ways to Contribute

- Improve OCR accuracy or add new pre-processing steps
- Extend multilingual language support
- Improve API performance or add new endpoints
- Fix bugs or improve error handling
- Improve documentation or add usage examples
- Add or improve tests
- Add your name to [CONTRIBUTORS.md](CONTRIBUTORS.md)

## Running Tests

```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with coverage report
pytest --cov=ocr_correction tests/
```

## Code Style

- Follow [PEP 8](https://pep8.org/) conventions.
- Maximum line length is **100 characters**.
- Run `flake8` before submitting:

  ```bash
  flake8 ocr_correction/ tests/ app.py
  ```

## Submitting a Pull Request

1. Commit your changes with a clear message:

   ```bash
   git add .
   git commit -m "feat: describe your change clearly"
   git push origin feature/your-feature-name
   ```

2. Open a Pull Request against the `master` branch and describe what you changed and why.

3. Ensure CI checks pass — the test suite and linter run automatically on every PR.

4. Wait for review — feedback will be given promptly.

---

⭐ If this project helped you, please consider starring the repository!
