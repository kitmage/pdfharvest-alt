"""Tests for pdfharvest.pdf_utils."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from pypdf import PdfReader, PdfWriter

from pdfharvest.exceptions import PDFError
from pdfharvest.pdf_utils import (
    extract_text_from_page,
    get_total_pages,
    ocr_page,
)


def _make_blank_pdf(path: Path, num_pages: int = 1) -> None:
    writer = PdfWriter()
    for _ in range(num_pages):
        writer.add_blank_page(width=72, height=72)
    with path.open("wb") as f:
        writer.write(f)


def test_get_total_pages(tmp_path: Path) -> None:
    pdf_path = tmp_path / "blank.pdf"
    _make_blank_pdf(pdf_path, num_pages=3)
    assert get_total_pages(pdf_path) == 3


def test_get_total_pages_single(tmp_path: Path) -> None:
    pdf_path = tmp_path / "one.pdf"
    _make_blank_pdf(pdf_path, num_pages=1)
    assert get_total_pages(pdf_path) == 1


def test_get_total_pages_raises_on_invalid_file(tmp_path: Path) -> None:
    not_pdf = tmp_path / "not.pdf"
    not_pdf.write_bytes(b"not a pdf")
    with pytest.raises(PDFError, match="Failed to read PDF"):
        get_total_pages(not_pdf)


def test_extract_text_from_page_blank(tmp_path: Path) -> None:
    pdf_path = tmp_path / "blank.pdf"
    _make_blank_pdf(pdf_path)
    reader = PdfReader(str(pdf_path))
    text = extract_text_from_page(reader, 0)
    assert text == ""


def test_ocr_page_returns_empty_on_convert_failure(tmp_path: Path) -> None:
    pdf_path = tmp_path / "x.pdf"
    _make_blank_pdf(pdf_path)
    with patch("pdfharvest.pdf_utils.convert_from_path") as convert:
        convert.side_effect = RuntimeError("poppler missing")
        result = ocr_page(pdf_path, 1, str(tmp_path))
    assert result == ""


def test_ocr_page_returns_empty_when_no_images(tmp_path: Path) -> None:
    pdf_path = tmp_path / "x.pdf"
    _make_blank_pdf(pdf_path)
    with patch("pdfharvest.pdf_utils.convert_from_path") as convert:
        convert.return_value = []
        result = ocr_page(pdf_path, 1, str(tmp_path))
    assert result == ""


def test_ocr_page_returns_text_from_tesseract(tmp_path: Path) -> None:
    pdf_path = tmp_path / "x.pdf"
    _make_blank_pdf(pdf_path)
    mock_image = MagicMock()
    with patch("pdfharvest.pdf_utils.convert_from_path") as convert:
        convert.return_value = [mock_image]
        with patch("pdfharvest.pdf_utils.pytesseract") as pyt:
            pyt.image_to_string.return_value = "extracted text"
            result = ocr_page(pdf_path, 1, str(tmp_path))
    assert result == "extracted text"
    mock_image.close.assert_called_once()


def test_ocr_page_closes_image_on_tesseract_error(tmp_path: Path) -> None:
    """When tesseract raises, image.close() is still called (in finally), then exception propagates."""
    pdf_path = tmp_path / "x.pdf"
    _make_blank_pdf(pdf_path)
    mock_image = MagicMock()
    with patch("pdfharvest.pdf_utils.convert_from_path") as convert:
        convert.return_value = [mock_image]
        with patch("pdfharvest.pdf_utils.pytesseract") as pyt:
            pyt.image_to_string.side_effect = Exception("tesseract error")
            with pytest.raises(Exception, match="tesseract error"):
                ocr_page(pdf_path, 1, str(tmp_path))
    mock_image.close.assert_called_once()
