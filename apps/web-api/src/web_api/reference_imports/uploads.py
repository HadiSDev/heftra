"""Saving an uploaded workbook to a temporary file until its import job has read it."""
from __future__ import annotations

import tempfile
from pathlib import Path
from typing import BinaryIO

CHUNK_BYTES = 1024 * 1024
ZIP_SIGNATURE = b"PK\x03\x04"
WORKBOOK_SUFFIX = ".xlsx"


class UploadTooLarge(Exception):
    """The upload is over the size limit."""


class NotAWorkbook(Exception):
    """The upload isn't an .xlsx workbook."""


def save_workbook(filename: str, stream: BinaryIO, *, max_bytes: int,
                  directory: str | None) -> Path:
    """The upload's path on disk; nothing is left behind when it is refused."""
    if not filename.lower().endswith(WORKBOOK_SUFFIX):
        raise NotAWorkbook(f"{filename} is not an {WORKBOOK_SUFFIX} file")
    with tempfile.NamedTemporaryFile(suffix=WORKBOOK_SUFFIX, dir=directory, delete=False) as out:
        path = Path(out.name)
        try:
            _copy(stream, out, max_bytes)
        except (UploadTooLarge, NotAWorkbook):
            out.close()
            path.unlink(missing_ok=True)
            raise
    return path


def _copy(stream: BinaryIO, out: BinaryIO, max_bytes: int) -> None:
    written = 0
    first = True
    while chunk := stream.read(CHUNK_BYTES):
        if first and not chunk.startswith(ZIP_SIGNATURE):
            raise NotAWorkbook("the file is not an Excel workbook")
        first = False
        written += len(chunk)
        if written > max_bytes:
            raise UploadTooLarge(f"the file is over {max_bytes // (1024 * 1024)} MB")
        out.write(chunk)
    if first:
        raise NotAWorkbook("the file is empty")
