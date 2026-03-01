"""Configuration constants and environment defaults for pdfharvest."""

import os
from pathlib import Path
from typing import Final

# Environment variable names
ENV_OPENROUTER_API_KEY: Final[str] = "OPENROUTER_API_KEY"
ENV_OPENROUTER_MODEL: Final[str] = "OPENROUTER_MODEL"
ENV_OPENROUTER_REFERER: Final[str] = "OPENROUTER_REFERER"
ENV_OPENROUTER_TITLE: Final[str] = "OPENROUTER_TITLE"
ENV_PDFHARVEST_STORAGE_DIR: Final[str] = "PDFHARVEST_STORAGE_DIR"

# Defaults
DEFAULT_OPENROUTER_MODEL: Final[str] = "google/gemini-2.5-flash"
DEFAULT_OPENROUTER_TITLE: Final[str] = "pdfharvest"
OPENROUTER_BASE_URL: Final[str] = "https://openrouter.ai/api/v1"

# Output formats
OUTPUT_FORMAT_CSV: Final[str] = "CSV"
OUTPUT_FORMAT_TSV: Final[str] = "TSV"
OUTPUT_FORMATS: Final[tuple[str, ...]] = (OUTPUT_FORMAT_TSV, OUTPUT_FORMAT_CSV)

# I/O
DEFAULT_CHUNK_SIZE: Final[int] = 4 * 1024 * 1024  # 4 MiB
DEFAULT_OCR_DPI: Final[int] = 200


def get_storage_dir() -> Path:
    """Return the configured storage directory for uploaded PDFs."""
    raw = os.getenv(ENV_PDFHARVEST_STORAGE_DIR)
    if raw:
        return Path(raw)
    return Path.cwd() / "data"
