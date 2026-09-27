"""Accepting an uploaded agreement PDF and recording it."""
from __future__ import annotations

from pathlib import PurePath

from sqlmodel import Session

from ..audit import record_audit
from ..db.models import Agreement, File
from ..storage.keys import agreement_key
from .constants import AGREEMENT_FILE_TYPE, AUDIT_AGREEMENT, PDF_SIGNATURE


class NotAPdf(ValueError):
    """The upload isn't a PDF."""


class AgreementTooLarge(ValueError):
    """The upload is over the size limit."""


def check_pdf(filename: str, data: bytes, max_bytes: int) -> None:
    if not filename.lower().endswith(".pdf") or not data.startswith(PDF_SIGNATURE):
        raise NotAPdf(f"{filename} is not a PDF")
    if len(data) > max_bytes:
        raise AgreementTooLarge(f"{filename} is over {max_bytes // (1024 * 1024)} MB")


def record_agreement(session: Session, company_id: str, filename: str, size: int,
                     uploaded_by: str) -> tuple[Agreement, str]:
    """The new agreement and its file row, flushed but not committed, and the key to store it at."""
    agreement = Agreement(company_id=company_id, file_id="", title=PurePath(filename).stem,
                          uploaded_by=uploaded_by)
    key = agreement_key(company_id, agreement.id)
    file_row = File(company_id=company_id, uploaded_by=uploaded_by, filename=filename,
                    file_type=AGREEMENT_FILE_TYPE, storage_path=key, file_size=size)
    session.add(file_row)
    session.flush()
    agreement.file_id = file_row.id
    session.add(agreement)
    record_audit(session, entity_type=AUDIT_AGREEMENT, entity_id=agreement.id, action="upload",
                 actor=uploaded_by, changes=[{"field": "file", "old": None, "new": filename}])
    session.flush()
    return agreement, key
