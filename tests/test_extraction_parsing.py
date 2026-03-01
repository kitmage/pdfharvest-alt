"""Tests for extraction parsing (no LLM)."""

from pdfharvest.extraction import (
    _build_page_context,
    _normalize_email_spacing,
    _pick_primary_text,
    _quality_score,
    parse_rows,
    serialize_rows,
    strip_code_fences,
)
from pdfharvest.config import OUTPUT_FORMAT_CSV, OUTPUT_FORMAT_TSV


def test_strip_code_fences_plain() -> None:
    assert strip_code_fences("a,b\n1,2") == "a,b\n1,2"
    assert strip_code_fences("  a,b  ") == "a,b"


def test_strip_code_fences_csv_fence() -> None:
    raw = "```csv\na,b\n1,2\n```"
    assert strip_code_fences(raw) == "a,b\n1,2"


def test_strip_code_fences_tsv_fence() -> None:
    raw = "```tsv\nx\ty\n1\t2\n```"
    assert strip_code_fences(raw) == "x\ty\n1\t2"


def test_parse_rows_empty() -> None:
    assert parse_rows("", ",") == []
    assert parse_rows("  \n  ", ",") == []


def test_parse_rows_csv() -> None:
    rows = parse_rows("a,b\n1,2", ",")
    assert rows == [["a", "b"], ["1", "2"]]


def test_parse_rows_skips_blank_rows() -> None:
    rows = parse_rows("a,b\n\n1,2\n  \n", ",")
    assert rows == [["a", "b"], ["1", "2"]]


def test_serialize_rows_csv() -> None:
    out = serialize_rows([["a", "b"], ["1", "2"]], OUTPUT_FORMAT_CSV)
    assert out == "a,b\n1,2"


def test_serialize_rows_tsv() -> None:
    out = serialize_rows([["x", "y"], ["1", "2"]], OUTPUT_FORMAT_TSV)
    assert "x\ty" in out and "1\t2" in out


def test_parse_rows_with_quoted_delimiters() -> None:
    rows = parse_rows('a,"b,c",d\n1,2,3', ",")
    assert rows == [["a", "b,c", "d"], ["1", "2", "3"]]


def test_parse_rows_page_number_header_lowercase() -> None:
    # Header row with first cell "page_number" is recognised
    rows = parse_rows("page_number,foo,bar\n1,alpha,beta", ",")
    assert rows[0][0].strip().lower() == "page_number"
    assert rows == [["page_number", "foo", "bar"], ["1", "alpha", "beta"]]


def test_normalize_email_spacing_repairs_common_artifacts() -> None:
    broken = "rschaab @ Covercoi nsu I ation . com"
    normalized = _normalize_email_spacing(broken)
    assert "@" in normalized
    assert ".com" in normalized


def test_quality_score_prefers_valid_email_tokenization() -> None:
    broken = "Contact: rschaab@Covercoi nsu I ation.com"
    clean = "Contact: rschaab@covercoinsulation.com"
    assert _quality_score(clean) > _quality_score(broken)


def test_pick_primary_text_chooses_higher_quality_source() -> None:
    vector_text = "Contact: rschaab@Covercoi nsu I ation.com"
    ocr_text = "Contact: rschaab@covercoinsulation.com"
    assert _pick_primary_text(vector_text, ocr_text) == ocr_text


def test_build_page_context_contains_dual_sources_and_primary() -> None:
    context = _build_page_context(
        3,
        "Vector: rschaab@Covercoi nsu I ation.com",
        "OCR: rschaab@covercoinsulation.com",
    )
    assert "[Page 3]" in context
    assert "Primary text:" in context
    assert "Vector extraction:" in context
    assert "OCR extraction:" in context
