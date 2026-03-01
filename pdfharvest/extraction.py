"""LLM-based extraction and CSV/TSV parsing."""

import csv
import io
import os
import re
import tempfile
from pathlib import Path
from typing import Callable, Iterator

from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pypdf import PdfReader

from pdfharvest.config import (
    ENV_OPENROUTER_REFERER,
    ENV_OPENROUTER_TITLE,
    DEFAULT_OPENROUTER_TITLE,
    OPENROUTER_BASE_URL,
    OUTPUT_FORMAT_CSV,
)
from pdfharvest.exceptions import ExtractionError
from pdfharvest.pdf_utils import extract_text_from_page, ocr_page

# Regex to strip optional markdown code fences around CSV/TSV
_CODE_FENCE_RE = re.compile(r"```(?:csv|tsv)?\s*([\s\S]*?)\s*```", re.IGNORECASE)


def strip_code_fences(text: str) -> str:
    """
    Remove optional markdown code fence wrapper from model output.

    Args:
        text: Raw model response.

    Returns:
        Inner content, or trimmed text if no fence found.
    """
    match = _CODE_FENCE_RE.search(text)
    if match:
        return match.group(1).strip()
    return text.strip()


def parse_rows(text: str, delimiter: str) -> list[list[str]]:
    """
    Parse CSV/TSV text into rows, stripping code fences and blank rows.

    Args:
        text: Raw tabular text.
        delimiter: Field delimiter (e.g. ',' or '\\t').

    Returns:
        List of rows, each row a list of stripped cells. Empty rows omitted.
    """
    cleaned = strip_code_fences(text)
    if not cleaned:
        return []
    reader = csv.reader(io.StringIO(cleaned), delimiter=delimiter)
    rows: list[list[str]] = []
    for row in reader:
        if not row or all(not (cell or "").strip() for cell in row):
            continue
        rows.append([(cell or "").strip() for cell in row])
    return rows


def _get_delimiter(output_format: str) -> str:
    """Return delimiter for the given output format."""
    return "," if output_format == OUTPUT_FORMAT_CSV else "\t"


def _build_llm(
    api_key: str,
    model: str,
) -> ChatOpenAI:
    """Build ChatOpenAI client for OpenRouter with optional headers."""
    referer = os.getenv(ENV_OPENROUTER_REFERER, "").strip()
    title = os.getenv(ENV_OPENROUTER_TITLE, DEFAULT_OPENROUTER_TITLE).strip()
    headers: dict[str, str] = {}
    if referer:
        headers["HTTP-Referer"] = referer
    if title:
        headers["X-Title"] = title
    return ChatOpenAI(
        api_key=api_key,
        base_url=OPENROUTER_BASE_URL,
        model=model,
        temperature=0,
        default_headers=headers or None,
    )


def _build_prompt() -> ChatPromptTemplate:
    """Return the per-page extraction prompt template."""
    return ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a precise data extraction assistant. "
                "Use only the provided PDF page content. "
                "Return results in {output_format} format. "
                "Include a column named page_number as the first column. "
                "If include_header is 'yes', include a header row. "
                "If include_header is 'no', do not include a header row. "
                "Use a consistent column order and field format on every page. "
                "Extract all data that matches the user request; do not omit fields. "
                "Do not wrap the output in code fences. "
                "If something is not present on that page, respond with 'Not found'.",
            ),
            (
                "human",
                "User request: {question}\n\ninclude_header: {include_header}\n\nPDF page content:\n{context}",
            ),
        ]
    )


def _iter_page_text(
    pdf_path: Path,
    reader: PdfReader,
    page_offset: int,
    limit_pages: int | None,
    temp_dir: str,
) -> Iterator[tuple[int, str]]:
    """
    Yield (one_based_page_number, page_text) for each page in range.
    
    Handles both vector (text-based) and raster (image-based) pages:
    - Vector pages: Extract native text directly
    - Raster pages: Use OCR to extract text from rendered images
    - Mixed pages: Prefer vector text, fall back to OCR if vector is empty
    """
    total = len(reader.pages)
    start = page_offset
    end = total if limit_pages is None else min(start + limit_pages, total)
    for idx in range(start, end):
        one_based = idx + 1
        # Try vector text extraction first (fast, accurate for text-based PDFs)
        vector_text = extract_text_from_page(reader, idx)
        
        # Always try OCR for raster pages, and also for pages with minimal vector text
        # (vector extraction might miss content in complex layouts or scanned pages)
        ocr_text = ocr_page(pdf_path, one_based, temp_dir)
        
        # Combine both sources: prefer vector if substantial, otherwise use OCR
        # If both exist, combine them (vector might have structure, OCR might have more content)
        if vector_text and len(vector_text) > 50:
            # Vector text is substantial - use it, but append OCR if it adds content
            if ocr_text and len(ocr_text) > len(vector_text) * 1.5:
                # OCR found significantly more - use OCR as primary
                page_text = ocr_text
            else:
                page_text = vector_text
        elif ocr_text:
            # OCR found content - use it
            page_text = ocr_text
        elif vector_text:
            # Only vector text (even if short) - use it
            page_text = vector_text
        else:
            # Both empty - still yield with empty text so LLM can note the page exists
            page_text = ""
        
        page_text = (page_text or "").strip()
        # Yield all pages, even if empty (LLM can handle empty pages)
        yield one_based, page_text


def run_extraction(
    pdf_path: Path,
    user_prompt: str,
    *,
    page_offset: int = 0,
    limit_pages: int | None = None,
    output_format: str = OUTPUT_FORMAT_CSV,
    api_key: str,
    model: str,
    progress_callback: Callable[[float, str], None] | None = None,
) -> tuple[list[list[str]], int, int]:
    """
    Run full extraction over the PDF and return merged rows and counts.

    Args:
        pdf_path: Path to the stored PDF.
        user_prompt: User's extraction request.
        page_offset: Zero-based index of first page to process.
        limit_pages: Max pages to process (None = all after offset).
        output_format: 'CSV' or 'TSV'.
        api_key: OpenRouter API key.
        model: Model name.
        progress_callback: Optional (progress_0_to_1, message) callback.

    Returns:
        (output_rows, extracted_pages_count, effective_total_pages).

    Raises:
        ExtractionError: If PDF is unreadable or extraction fails critically.
    """
    reader = PdfReader(str(pdf_path))
    total_pages = len(reader.pages)
    remaining = total_pages - page_offset
    effective_total = min(remaining, limit_pages) if limit_pages else remaining
    if effective_total <= 0:
        return [], 0, effective_total

    llm = _build_llm(api_key, model)
    prompt = _build_prompt()
    delimiter = _get_delimiter(output_format)
    output_rows: list[list[str]] = []
    header: list[str] | None = None
    extracted_pages = 0
    processed = 0

    with tempfile.TemporaryDirectory(dir=str(pdf_path.parent)) as temp_dir:
        for one_based, page_text in _iter_page_text(
            pdf_path, reader, page_offset, limit_pages, temp_dir
        ):
            processed += 1
            if progress_callback:
                progress_callback(
                    processed / max(effective_total, 1),
                    f"Extracting page {processed}/{effective_total}",
                )
            include_header = "yes" if header is None else "no"
            # If page appears empty, give LLM context about it
            if not page_text:
                context = f"[Page {one_based}]\n[This page appears to be empty or contains only images/graphics with no extractable text.]"
            else:
                context = f"[Page {one_based}]\n{page_text}"
            messages = prompt.format_messages(
                question=user_prompt,
                context=context,
                include_header=include_header,
                output_format=output_format,
            )
            try:
                result = llm.invoke(messages)
            except Exception as e:
                raise ExtractionError(f"LLM invocation failed: {e}") from e
            page_output = getattr(result, "content", None) or str(result)
            if not page_output:
                continue
            rows = parse_rows(page_output, delimiter)
            if not rows:
                continue
            page_has_data = False
            for row in rows:
                if not row:
                    continue
                if header is None and row[0].strip().lower() == "page_number":
                    header = row
                    output_rows.append(header)
                    continue
                if header and row == header:
                    continue
                # Ensure first column (page_number) is the actual PDF page number
                data_row = [str(one_based)] + row[1:]
                output_rows.append(data_row)
                page_has_data = True
            if page_has_data:
                extracted_pages += 1

    return output_rows, extracted_pages, effective_total


def serialize_rows(rows: list[list[str]], output_format: str) -> str:
    """
    Serialize rows to CSV or TSV string.

    Args:
        rows: List of row lists.
        output_format: 'CSV' or 'TSV'.

    Returns:
        Final text (no trailing newline).
    """
    delimiter = _get_delimiter(output_format)
    buffer = io.StringIO()
    writer = csv.writer(
        buffer,
        delimiter=delimiter,
        quoting=csv.QUOTE_MINIMAL,
        lineterminator="\n",
    )
    for row in rows:
        writer.writerow(row)
    return buffer.getvalue().rstrip("\n")
