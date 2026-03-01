"""Tests for run_extraction and extraction pipeline (with mocked LLM)."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pypdf import PdfWriter

from pdfharvest.config import OUTPUT_FORMAT_CSV, OUTPUT_FORMAT_TSV
from pdfharvest.exceptions import ExtractionError
from pdfharvest.extraction import run_extraction


def _make_blank_pdf(path: Path, num_pages: int = 1) -> None:
    writer = PdfWriter()
    for _ in range(num_pages):
        writer.add_blank_page(width=72, height=72)
    with path.open("wb") as f:
        writer.write(f)


def test_run_extraction_zero_effective_pages_returns_empty(tmp_path: Path) -> None:
    pdf_path = tmp_path / "blank.pdf"
    _make_blank_pdf(pdf_path)
    # page_offset beyond or limit 0: no pages to process
    rows, extracted, total = run_extraction(
        pdf_path,
        "extract x",
        page_offset=1,
        limit_pages=None,
        output_format=OUTPUT_FORMAT_CSV,
        api_key="fake",
        model="fake",
    )
    assert rows == []
    assert extracted == 0
    assert total == 0


def test_run_extraction_with_mocked_ocr_and_llm(tmp_path: Path) -> None:
    pdf_path = tmp_path / "blank.pdf"
    _make_blank_pdf(pdf_path)
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = "page_number,value\n1,extracted"
    mock_llm.invoke.return_value = mock_response

    with patch("pdfharvest.extraction.ocr_page", return_value="page text here"):
        with patch("pdfharvest.extraction._build_llm", return_value=mock_llm):
            rows, extracted, total = run_extraction(
                pdf_path,
                "extract value",
                page_offset=0,
                limit_pages=1,
                output_format=OUTPUT_FORMAT_CSV,
                api_key="key",
                model="model",
            )
    assert len(rows) == 2
    assert rows[0] == ["page_number", "value"]
    assert rows[1] == ["1", "extracted"]
    assert extracted == 1
    assert total == 1


def test_run_extraction_calls_progress_callback(tmp_path: Path) -> None:
    pdf_path = tmp_path / "blank.pdf"
    _make_blank_pdf(pdf_path)
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content="page_number,a\n1,b")
    progress_calls: list[tuple[float, str]] = []

    def capture(p: float, t: str) -> None:
        progress_calls.append((p, t))

    with patch("pdfharvest.extraction.ocr_page", return_value="x"):
        with patch("pdfharvest.extraction._build_llm", return_value=mock_llm):
            run_extraction(
                pdf_path,
                "q",
                limit_pages=1,
                api_key="k",
                model="m",
                progress_callback=capture,
            )
    assert len(progress_calls) >= 1
    assert progress_calls[0][0] == 1.0
    assert "1/1" in progress_calls[0][1]


def test_run_extraction_tsv_format(tmp_path: Path) -> None:
    pdf_path = tmp_path / "blank.pdf"
    _make_blank_pdf(pdf_path)
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content="page_number\tval\n1\tdata")
    with patch("pdfharvest.extraction.ocr_page", return_value="text"):
        with patch("pdfharvest.extraction._build_llm", return_value=mock_llm):
            rows, _, _ = run_extraction(
                pdf_path,
                "q",
                limit_pages=1,
                output_format=OUTPUT_FORMAT_TSV,
                api_key="k",
                model="m",
            )
    assert rows[0] == ["page_number", "val"]
    assert rows[1] == ["1", "data"]


def test_run_extraction_skips_duplicate_header_row(tmp_path: Path) -> None:
    pdf_path = tmp_path / "blank.pdf"
    _make_blank_pdf(pdf_path)
    mock_llm = MagicMock()
    # First page: header + data; second page could send header again - we skip duplicate
    mock_llm.invoke.return_value = MagicMock(
        content="page_number,name\n1,Alice\npage_number,name\n2,Bob"
    )
    with patch("pdfharvest.extraction.ocr_page", return_value="page text"):
        with patch("pdfharvest.extraction._build_llm", return_value=mock_llm):
            # One page only - so single invoke
            rows, _, _ = run_extraction(
                pdf_path,
                "q",
                limit_pages=1,
                api_key="k",
                model="m",
            )
    assert rows[0] == ["page_number", "name"]
    assert ["1", "Alice"] in rows


def test_run_extraction_skips_page_when_llm_returns_empty(tmp_path: Path) -> None:
    """When LLM returns no content for a page, that page contributes no rows."""
    pdf_path = tmp_path / "blank.pdf"
    _make_blank_pdf(pdf_path)
    mock_llm = MagicMock()
    mock_response = MagicMock()
    mock_response.content = ""
    mock_response.__str__ = lambda self: ""  # getattr(..., "content") or str(result) -> ""
    mock_llm.invoke.return_value = mock_response
    with patch("pdfharvest.extraction.ocr_page", return_value="text"):
        with patch("pdfharvest.extraction._build_llm", return_value=mock_llm):
            rows, extracted, total = run_extraction(
                pdf_path,
                "q",
                limit_pages=1,
                api_key="k",
                model="m",
            )
    assert rows == []
    assert extracted == 0
    assert total == 1


def test_run_extraction_page_number_is_actual_pdf_page(tmp_path: Path) -> None:
    """With page_offset=2, first data row's page_number column is 3 (one-based), not 1."""
    pdf_path = tmp_path / "blank.pdf"
    _make_blank_pdf(pdf_path, num_pages=5)
    mock_llm = MagicMock()
    mock_llm.invoke.return_value = MagicMock(content="page_number,val\n1,ignored")
    with patch("pdfharvest.extraction.ocr_page", return_value="text"):
        with patch("pdfharvest.extraction._build_llm", return_value=mock_llm):
            rows, _, _ = run_extraction(
                pdf_path,
                "q",
                page_offset=2,
                limit_pages=1,
                api_key="k",
                model="m",
            )
    assert rows[0] == ["page_number", "val"]
    assert rows[1][0] == "3", "first column should be actual PDF page number (page 3)"

def test_run_extraction_raises_on_llm_failure(tmp_path: Path) -> None:
    pdf_path = tmp_path / "blank.pdf"
    _make_blank_pdf(pdf_path)
    mock_llm = MagicMock()
    mock_llm.invoke.side_effect = RuntimeError("API error")
    with patch("pdfharvest.extraction.ocr_page", return_value="x"):
        with patch("pdfharvest.extraction._build_llm", return_value=mock_llm):
            with pytest.raises(ExtractionError, match="LLM invocation failed"):
                run_extraction(
                    pdf_path,
                    "q",
                    limit_pages=1,
                    api_key="k",
                    model="m",
                )
