"""
Streamlit UI entrypoint for pdfharvest.

Delegates storage, PDF, validation, and extraction to the pdfharvest package.
"""

from __future__ import annotations

import os
from pathlib import Path

import pandas as pd
import streamlit as st

from pdfharvest import (
    OUTPUT_FORMAT_CSV,
    OUTPUT_FORMATS,
    get_storage_dir,
)
from pdfharvest.config import (
    ENV_OPENROUTER_API_KEY,
    ENV_OPENROUTER_MODEL,
    DEFAULT_OPENROUTER_MODEL,
)
from pdfharvest.exceptions import (
    ExtractionError,
    PDFError,
    StorageError,
    ValidationError,
)
from pdfharvest.extraction import run_extraction, serialize_rows
from pdfharvest.storage import remove_if_exists, save_upload_to_storage
from pdfharvest.pdf_utils import get_total_pages
from pdfharvest.validation import validate_page_range

st.set_page_config(page_title="pdfharvest", layout="wide")

st.title("PDF Harvest")
st.write("Upload a PDF and provide a prompt describing what to extract.")

with st.sidebar:
    st.header("Settings")
    api_key_input = st.text_input("OPENROUTER_API_KEY", type="password")
    model_name = st.text_input(
        "Model",
        value=os.getenv(ENV_OPENROUTER_MODEL, DEFAULT_OPENROUTER_MODEL),
    )
    limit_pages_input = st.text_input(
        "Limit pages (optional)",
        value="3",
        placeholder="e.g. 10",
        help="Leave blank to process all pages.",
    )
    page_offset_input = st.text_input(
        "Page offset (optional)",
        value="",
        placeholder="e.g. 0",
        help="Number of pages to skip before processing.",
    )
    output_format = st.selectbox(
        "Output format",
        options=list(OUTPUT_FORMATS),
        index=0,
    )

uploaded_file = st.file_uploader("PDF file", type=["pdf"])
user_prompt = st.text_area(
    "Extraction prompt",
    placeholder="Example: Extract the invoice number, date, vendor, and total as JSON.",
    height=150,
)

extract_button = st.button(
    "Extract",
    type="primary",
    disabled=uploaded_file is None or not (user_prompt or "").strip(),
)

storage_dir = get_storage_dir()

if extract_button:
    api_key = api_key_input or os.getenv(ENV_OPENROUTER_API_KEY, "")
    if not api_key:
        st.error("Missing OPENROUTER_API_KEY. Set it in the sidebar or environment.")
        st.stop()

    stored_path: Path | None = None
    try:
        with st.spinner("Reading PDF..."):
            try:
                stored_path = save_upload_to_storage(uploaded_file, storage_dir)
            except StorageError as e:
                st.error(str(e))
                st.stop()

            try:
                total_pages = get_total_pages(stored_path)
            except PDFError as e:
                st.error(str(e))
                st.stop()

            try:
                page_offset, limit_pages = validate_page_range(
                    page_offset_input,
                    limit_pages_input,
                    total_pages,
                )
            except ValidationError as e:
                st.error(str(e))
                st.stop()

        def progress_cb(progress: float, text: str) -> None:
            progress_bar.progress(progress, text=text)

        progress_bar = st.progress(0.0, text="Extracting page 1/1")
        with st.spinner("Extracting..."):
            try:
                output_rows, extracted_pages, effective_total = run_extraction(
                    stored_path,
                    user_prompt,
                    page_offset=page_offset,
                    limit_pages=limit_pages,
                    output_format=output_format,
                    api_key=api_key,
                    model=model_name,
                    progress_callback=progress_cb,
                )
            except ExtractionError as e:
                st.error(str(e))
                st.stop()

        progress_bar.empty()

        if not output_rows:
            st.error("No text could be extracted from the PDF.")
            st.stop()

        output_text = serialize_rows(output_rows, output_format)
        st.session_state["result"] = {
            "rows": output_rows,
            "text": output_text,
            "extracted_pages": extracted_pages,
            "effective_total": effective_total,
            "output_format": output_format,
        }
    finally:
        remove_if_exists(stored_path)

# Show table and download when we have a result (this run or after download click)
if "result" in st.session_state:
    result = st.session_state["result"]
    st.subheader("Result")
    st.caption(
        f"Pages scanned: {result['extracted_pages']} of {result['effective_total']}"
    )
    # First row as header, rest as data; normalize column count (LLM may return uneven rows)
    rows = result["rows"]
    if rows:
        max_cols = max(len(r) for r in rows)
        header = list(rows[0]) + [f"col_{i}" for i in range(len(rows[0]), max_cols)]
        data = [(row + [""] * max_cols)[:max_cols] for row in rows[1:]]
        df = pd.DataFrame(data, columns=header)
        st.dataframe(df, use_container_width=True)
    file_ext = (
        "csv"
        if result["output_format"] == OUTPUT_FORMAT_CSV
        else "tsv"
    )
    mime_type = (
        "text/csv"
        if result["output_format"] == OUTPUT_FORMAT_CSV
        else "text/tab-separated-values"
    )
    st.download_button(
        label="Download result",
        data=result["text"],
        file_name=f"extraction.{file_ext}",
        mime=mime_type,
    )
