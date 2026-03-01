"""Tests for pdfharvest.config."""

from pathlib import Path

import pytest

from pdfharvest.config import (
    ENV_PDFHARVEST_STORAGE_DIR,
    get_storage_dir,
    OUTPUT_FORMAT_CSV,
    OUTPUT_FORMAT_TSV,
    OUTPUT_FORMATS,
)


def test_get_storage_dir_default(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv(ENV_PDFHARVEST_STORAGE_DIR, raising=False)
    result = get_storage_dir()
    assert result == Path.cwd() / "data"


def test_get_storage_dir_from_env(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv(ENV_PDFHARVEST_STORAGE_DIR, "/custom/storage")
    result = get_storage_dir()
    assert result == Path("/custom/storage")


def test_output_formats_constants() -> None:
    assert OUTPUT_FORMAT_CSV == "CSV"
    assert OUTPUT_FORMAT_TSV == "TSV"
    assert OUTPUT_FORMATS == (OUTPUT_FORMAT_CSV, OUTPUT_FORMAT_TSV)
