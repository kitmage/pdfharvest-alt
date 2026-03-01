"""PDF reading and OCR utilities."""

from pathlib import Path

from pdf2image import convert_from_path
import pytesseract
from pypdf import PdfReader

from pdfharvest.config import DEFAULT_OCR_DPI

# Higher DPI for better OCR quality on raster/scanned pages
OCR_DPI_RASTER: int = 300  # Higher quality for scanned documents
from pdfharvest.exceptions import PDFError


def get_total_pages(pdf_path: Path) -> int:
    """
    Return the number of pages in the PDF.

    Args:
        pdf_path: Path to the PDF file.

    Returns:
        Page count (>= 0).

    Raises:
        PDFError: If the file cannot be read as a PDF.
    """
    try:
        reader = PdfReader(str(pdf_path))
        return len(reader.pages)
    except Exception as e:
        raise PDFError(f"Failed to read PDF: {e}") from e


def extract_text_from_page(reader: PdfReader, page_index: int) -> str:
    """
    Extract text from a single page using pypdf (no OCR).

    Args:
        reader: Open PdfReader instance.
        page_index: Zero-based page index.

    Returns:
        Extracted text, or empty string if none.
    """
    try:
        page = reader.pages[page_index]
        text = page.extract_text() or ""
        return text.strip()
    except Exception:
        return ""


def ocr_page(
    pdf_path: Path,
    page_number: int,
    temp_dir: str,
    dpi: int | None = None,
) -> str:
    """
    Run Tesseract OCR on a single PDF page (raster or mixed content).

    Args:
        pdf_path: Path to the PDF file.
        page_number: One-based page number (as in pypdf enumeration).
        temp_dir: Directory for temporary rendered images.
        dpi: Resolution for rendering. If None, uses OCR_DPI_RASTER (300) for better quality.

    Returns:
        OCR text for the page, or empty string if OCR fails or yields nothing.
    """
    if dpi is None:
        dpi = OCR_DPI_RASTER
    try:
        images = convert_from_path(
            str(pdf_path),
            first_page=page_number,
            last_page=page_number,
            dpi=dpi,
            fmt="png",
            output_folder=temp_dir,
        )
    except Exception:
        return ""
    if not images:
        return ""
    image = images[0]
    try:
        # Try multiple OCR strategies for better coverage
        # PSM 6 = Assume uniform block of text (good for most pages)
        # PSM 11 = Sparse text (fallback for complex layouts)
        # PSM 3 = Fully automatic page segmentation (most flexible)
        # PSM 1 = Automatic page segmentation with OSD (orientation detection)
        
        strategies = [
            ("--psm 6", "uniform text"),
            ("--psm 3", "auto segmentation"),
            ("--psm 11", "sparse text"),
            ("--psm 1", "auto with OSD"),
        ]
        
        best_text = ""
        for config, _desc in strategies:
            try:
                text = pytesseract.image_to_string(image, config=config) or ""
                text = text.strip()
                # Prefer longer results (more content detected)
                if len(text) > len(best_text):
                    best_text = text
                # If we got substantial text, use it
                if len(text) > 100:
                    return text
            except Exception:
                continue
        
        return best_text
    except Exception:
        return ""
    finally:
        try:
            image.close()
        except Exception:
            pass
