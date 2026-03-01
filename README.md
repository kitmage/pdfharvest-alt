# pdfharvest

AGPLv3-licensed Streamlit app that uses LangChain to extract structured data from PDFs based on a user prompt.

## Project structure

- `app.py` – Streamlit UI entrypoint; delegates to the `pdfharvest` package.
- `pdfharvest/` – Core library:
  - `config.py` – Environment and constants.
  - `exceptions.py` – Domain exceptions (`StorageError`, `PDFError`, `ValidationError`, `ExtractionError`).
  - `storage.py` – Saving uploads and cleanup.
  - `pdf_utils.py` – PDF page count, text extraction, OCR.
  - `validation.py` – Page range and input validation.
  - `extraction.py` – Parsing (CSV/TSV), LLM prompt, and extraction pipeline.
- `tests/` – Unit tests for validation and extraction parsing. Run with: `pip install -r requirements-dev.txt && pytest tests/ -v`. Coverage: `pytest tests/ --cov=pdfharvest --cov-report=term-missing`

## Features
- Upload a PDF
- Enter a prompt describing what to extract
- Uses LangChain to parse the PDF and answer with extracted data
- Displays and allows download of the result

## Requirements
- Python 3.10+
- An OpenRouter API key

## Quickstart
```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

export OPENROUTER_API_KEY="your_key_here"
streamlit run app.py
```

## Docker
```bash
cp .env.example .env
cp -rf .streamlit.example .streamlit # If you'd like to configure the max upload limit
docker compose up --build
```

## Production (Traefik + Certbot)
```bash
cp .env.example .env
# set DOMAIN and CERTBOT_EMAIL in .env
docker compose -f docker-compose.production.yaml up -d --build
```

## Configuration
Environment variables:
- `OPENROUTER_API_KEY`: API key for OpenRouter.
- `OPENROUTER_MODEL`: Optional, default is `openai/gpt-4o-mini`.
- `OPENROUTER_REFERER`: Optional, HTTP referer for OpenRouter usage tracking.
- `OPENROUTER_TITLE`: Optional, app title for OpenRouter usage tracking.
- `PDFHARVEST_STORAGE_DIR`: Optional, default is `./data`.

## Notes
- Uploaded PDFs are written to `./data` (or `PDFHARVEST_STORAGE_DIR`) and deleted after extraction.
- The app reads PDFs page-by-page and uses Tesseract OCR when a page has no extractable text.
- Extraction runs per page and then merges results into a final response.
- Streamlit upload limit is set to 2 GB via `.streamlit/config.toml`.

## OCR Dependencies
Tesseract and Poppler must be installed on the host:
- macOS: `brew install tesseract poppler`
- Ubuntu/Debian: `sudo apt-get install tesseract-ocr poppler-utils`

## License
This project is licensed under the GNU Affero General Public License v3.0.
