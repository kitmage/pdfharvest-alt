"""Input validation for page range and settings."""

from __future__ import annotations

from pdfharvest.exceptions import ValidationError


def validate_page_range(
    page_offset_raw: str,
    limit_pages_raw: str,
    total_pages: int,
) -> tuple[int, int | None]:
    """
    Parse and validate page offset and limit against total pages.

    Args:
        page_offset_raw: User input for page offset (e.g. "0").
        limit_pages_raw: User input for page limit (e.g. "10" or "").
        total_pages: Total number of pages in the PDF.

    Returns:
        (page_offset, limit_pages). limit_pages is None if no limit.

    Raises:
        ValidationError: If total_pages <= 0, or inputs are invalid, or
            offset >= total_pages.
    """
    if total_pages <= 0:
        raise ValidationError("PDF has no pages.")

    limit_pages: int | None = None
    if limit_pages_raw.strip():
        try:
            limit_pages = int(limit_pages_raw.strip())
            if limit_pages <= 0:
                raise ValueError("must be positive")
        except ValueError:
            raise ValidationError("Limit pages must be a positive integer.") from None

    page_offset = 0
    if page_offset_raw.strip():
        try:
            page_offset = int(page_offset_raw.strip())
            if page_offset < 0:
                raise ValueError("must be non-negative")
        except ValueError:
            raise ValidationError("Page offset must be a non-negative integer.") from None

    if page_offset >= total_pages:
        raise ValidationError("Page offset is beyond the total number of pages.")

    return page_offset, limit_pages
