"""Tests for pdfharvest.validation."""

import pytest

from pdfharvest.exceptions import ValidationError
from pdfharvest.validation import validate_page_range


def test_validate_page_range_no_limit() -> None:
    page_offset, limit_pages = validate_page_range("", "", total_pages=10)
    assert page_offset == 0
    assert limit_pages is None


def test_validate_page_range_with_limit() -> None:
    page_offset, limit_pages = validate_page_range("0", "5", total_pages=10)
    assert page_offset == 0
    assert limit_pages == 5


def test_validate_page_range_with_offset() -> None:
    page_offset, limit_pages = validate_page_range("3", "", total_pages=10)
    assert page_offset == 3
    assert limit_pages is None


def test_validate_page_range_offset_and_limit() -> None:
    page_offset, limit_pages = validate_page_range("2", "4", total_pages=10)
    assert page_offset == 2
    assert limit_pages == 4


def test_validate_page_range_zero_pages_raises() -> None:
    with pytest.raises(ValidationError, match="no pages"):
        validate_page_range("", "", total_pages=0)


def test_validate_page_range_negative_offset_raises() -> None:
    with pytest.raises(ValidationError, match="non-negative"):
        validate_page_range("-1", "", total_pages=10)


def test_validate_page_range_offset_beyond_total_raises() -> None:
    with pytest.raises(ValidationError, match="beyond"):
        validate_page_range("10", "", total_pages=10)


def test_validate_page_range_invalid_limit_raises() -> None:
    with pytest.raises(ValidationError, match="positive integer"):
        validate_page_range("", "x", total_pages=10)
    with pytest.raises(ValidationError, match="positive integer"):
        validate_page_range("", "0", total_pages=10)
