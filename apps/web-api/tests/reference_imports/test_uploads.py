"""An uploaded workbook is saved within its size limit, or refused leaving nothing behind."""
from __future__ import annotations

import io

import pytest

from web_api.reference_imports.uploads import NotAWorkbook, UploadTooLarge, save_workbook

WORKBOOK_BYTES = b"PK\x03\x04" + b"x" * 100


def test_a_workbook_is_saved(tmp_path):
    path = save_workbook("CEDA.xlsx", io.BytesIO(WORKBOOK_BYTES), max_bytes=1000,
                         directory=str(tmp_path))

    assert path.read_bytes() == WORKBOOK_BYTES
    assert path.parent == tmp_path


def test_a_file_over_the_limit_is_refused(tmp_path):
    with pytest.raises(UploadTooLarge):
        save_workbook("CEDA.xlsx", io.BytesIO(WORKBOOK_BYTES), max_bytes=50,
                      directory=str(tmp_path))

    assert list(tmp_path.iterdir()) == []


def test_another_extension_is_refused(tmp_path):
    with pytest.raises(NotAWorkbook, match="not an .xlsx"):
        save_workbook("CEDA.pdf", io.BytesIO(WORKBOOK_BYTES), max_bytes=1000,
                      directory=str(tmp_path))


def test_content_that_is_not_a_zip_is_refused(tmp_path):
    with pytest.raises(NotAWorkbook):
        save_workbook("CEDA.xlsx", io.BytesIO(b"%PDF-1.7"), max_bytes=1000,
                      directory=str(tmp_path))

    assert list(tmp_path.iterdir()) == []


def test_an_empty_file_is_refused(tmp_path):
    with pytest.raises(NotAWorkbook, match="empty"):
        save_workbook("CEDA.xlsx", io.BytesIO(b""), max_bytes=1000, directory=str(tmp_path))
