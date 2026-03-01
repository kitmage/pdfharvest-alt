"""Custom exceptions for pdfharvest with clear, domain-specific semantics."""


class PDFHarvestError(Exception):
    """Base exception for all pdfharvest errors."""

    pass


class StorageError(PDFHarvestError):
    """Raised when file storage operations fail."""

    pass


class PDFError(PDFHarvestError):
    """Raised when PDF reading or parsing fails."""

    pass


class ValidationError(PDFHarvestError):
    """Raised when user or configuration input is invalid."""

    pass


class ExtractionError(PDFHarvestError):
    """Raised when LLM or extraction pipeline fails."""

    pass
