"""Tests for pdfharvest.storage."""

from io import BytesIO
from pathlib import Path

import pytest

from pdfharvest.exceptions import StorageError
from pdfharvest.storage import remove_if_exists, save_upload_to_storage


def test_save_upload_to_storage_creates_file(tmp_path: Path) -> None:
    content = b"fake pdf content"
    stream = BytesIO(content)
    result = save_upload_to_storage(stream, tmp_path)
    assert result.parent == tmp_path
    assert result.suffix == ".pdf"
    assert result.read_bytes() == content


def test_save_upload_to_storage_creates_parent_dirs(tmp_path: Path) -> None:
    storage_dir = tmp_path / "a" / "b" / "c"
    stream = BytesIO(b"x")
    result = save_upload_to_storage(stream, storage_dir)
    assert storage_dir.exists()
    assert result.read_bytes() == b"x"


def test_save_upload_to_storage_respects_chunk_size(tmp_path: Path) -> None:
    stream = BytesIO(b"ab")
    save_upload_to_storage(stream, tmp_path, chunk_size=1)
    files = list(tmp_path.glob("*.pdf"))
    assert len(files) == 1
    assert files[0].read_bytes() == b"ab"


def test_save_upload_to_storage_raises_on_write_error(tmp_path: Path) -> None:
    """When storage_dir is an existing file, mkdir/open fails with OSError."""
    stream = BytesIO(b"x")
    not_a_dir = tmp_path / "notadir"
    not_a_dir.write_text("")
    with pytest.raises(StorageError, match="Failed to write"):
        save_upload_to_storage(stream, not_a_dir)


def test_remove_if_exists_none() -> None:
    remove_if_exists(None)


def test_remove_if_exists_missing_file(tmp_path: Path) -> None:
    missing = tmp_path / "nonexistent.pdf"
    remove_if_exists(missing)


def test_remove_if_exists_removes_file(tmp_path: Path) -> None:
    f = tmp_path / "file.pdf"
    f.write_bytes(b"x")
    assert f.exists()
    remove_if_exists(f)
    assert not f.exists()
