"""Temporary storage for uploaded PDFs during extraction."""

import uuid
from pathlib import Path
from typing import BinaryIO

from pdfharvest.config import DEFAULT_CHUNK_SIZE
from pdfharvest.exceptions import StorageError


def save_upload_to_storage(
    stream: BinaryIO,
    storage_dir: Path,
    *,
    chunk_size: int = DEFAULT_CHUNK_SIZE,
) -> Path:
    """
    Persist an uploaded file stream to storage_dir with a unique name.

    Args:
        stream: Readable binary stream (e.g. from Streamlit file_uploader).
        storage_dir: Directory to write into; created if missing.
        chunk_size: Read/write chunk size in bytes.

    Returns:
        Path to the written file.

    Raises:
        StorageError: If directory creation or write fails.
    """
    try:
        storage_dir.mkdir(parents=True, exist_ok=True)
    except OSError as e:
        raise StorageError(f"Failed to write to {storage_dir}: {e}") from e
    file_name = f"{uuid.uuid4().hex}.pdf"
    target_path = storage_dir / file_name
    try:
        stream.seek(0)
        with target_path.open("wb") as f:
            while True:
                chunk = stream.read(chunk_size)
                if not chunk:
                    break
                f.write(chunk)
        return target_path
    except OSError as e:
        raise StorageError(f"Failed to write to {storage_dir}: {e}") from e


def remove_if_exists(path: Path | None) -> None:
    """
    Remove a file if it exists. Ignore errors (e.g. already deleted).

    Args:
        path: File path to remove, or None (no-op).
    """
    if path is None:
        return
    if not path.exists():
        return
    try:
        path.unlink()
    except OSError:
        pass
