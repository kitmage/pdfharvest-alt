"""Tests for pdfharvest.exceptions."""

import pytest

from pdfharvest.exceptions import (
    ExtractionError,
    PDFError,
    PDFHarvestError,
    StorageError,
    ValidationError,
)


@pytest.mark.parametrize(
    ("exc_class", "message"),
    [
        (PDFHarvestError, "base"),
        (StorageError, "write failed"),
        (PDFError, "read failed"),
        (ValidationError, "invalid input"),
        (ExtractionError, "LLM failed"),
    ],
)
def test_exception_raise_and_catch(exc_class: type[PDFHarvestError], message: str) -> None:
    with pytest.raises(exc_class) as exc_info:
        raise exc_class(message)
    assert str(exc_info.value) == message


def test_domain_exceptions_inherit_from_base() -> None:
    assert issubclass(StorageError, PDFHarvestError)
    assert issubclass(PDFError, PDFHarvestError)
    assert issubclass(ValidationError, PDFHarvestError)
    assert issubclass(ExtractionError, PDFHarvestError)
