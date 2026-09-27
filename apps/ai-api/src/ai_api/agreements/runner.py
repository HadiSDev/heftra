"""Claiming pending agreements and reading them into a header and draft terms."""
from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime, timedelta, timezone

from sqlalchemy import or_
from sqlalchemy.engine import Engine
from sqlmodel import Session, col, select

from web_api.agreements.status import settle_status
from web_api.db.models import Agreement, AgreementStatus, File
from web_api.storage.blocking import run_blocking
from web_api.storage.errors import StorageUnavailable, StoredFileMissing
from web_api.storage.store import FileStore

from .. import config
from .extract import AgreementUnreadable, Complete, read_agreement
from .header import apply_header, supplier_country
from .pages import UnreadablePdf, agreement_pages
from .scope_categories import category_suggester
from .store_terms import replace_drafts
from .supplier import link_vendor

logger = logging.getLogger("ai_api.agreements")

_EXPECTED = (StorageUnavailable, StoredFileMissing, UnreadablePdf, AgreementUnreadable)


def pending_agreements(session: Session, limit: int) -> list[Agreement]:
    """Pending agreements, and ones left reading longer than the stale timeout, oldest first."""
    stale = datetime.now(timezone.utc) - timedelta(minutes=config.AGREEMENT_STALE_CLAIM_MINUTES)
    return list(session.exec(
        select(Agreement).where(or_(
            Agreement.status == AgreementStatus.PENDING.value,
            (Agreement.status == AgreementStatus.READING.value)
            & (col(Agreement.read_started_at) < stale),
        ))
        .order_by(col(Agreement.created_at), col(Agreement.id))
        .limit(limit)
    ).all())


def read_pending(engine: Engine, store: FileStore, complete: Complete, *,
                 limit: int, suggest_for: Callable = category_suggester) -> dict[str, int]:
    """Read up to `limit` pending agreements; counts read and failed ones."""
    with Session(engine) as session:
        ids = [agreement.id for agreement in pending_agreements(session, limit)]
    counts = {"read": 0, "failed": 0}
    for agreement_id in ids:
        outcome = read_one(engine, agreement_id, store, complete, suggest_for=suggest_for)
        counts[outcome] += 1
    return counts


def read_one(engine: Engine, agreement_id: str, store: FileStore, complete: Complete, *,
             suggest_for: Callable = category_suggester) -> str:
    """Read one agreement; returns "read", or "failed" with its error recorded."""
    with Session(engine) as session:
        agreement = session.get(Agreement, agreement_id)
        _claim(session, agreement)
        try:
            _read(session, agreement, store, complete, suggest_for)
        except _EXPECTED as error:
            session.rollback()
            _fail(session, agreement_id, str(error))
            return "failed"
        except Exception as error:  # noqa: BLE001
            session.rollback()
            logger.exception("agreement %s could not be read", agreement_id)
            _fail(session, agreement_id, f"Unexpected error: {error}")
            return "failed"
        session.commit()
        return "read"


def _claim(session: Session, agreement: Agreement) -> None:
    agreement.status = AgreementStatus.READING.value
    agreement.read_started_at = datetime.now(timezone.utc)
    agreement.read_attempts += 1
    session.add(agreement)
    session.commit()


def _read(session: Session, agreement: Agreement, store: FileStore, complete: Complete,
          suggest_for: Callable) -> None:
    file_row = session.get(File, agreement.file_id)
    if file_row is None:
        raise StoredFileMissing(agreement.file_id)
    pages = agreement_pages(run_blocking(store.get(file_row.storage_path)))
    read = read_agreement(pages, complete=complete)
    apply_header(agreement, file_row, read.header)
    if agreement.vendor_id is None:
        agreement.vendor_id = link_vendor(
            session, agreement.company_id, vat_number=agreement.supplier_vat_number,
            country_code=supplier_country(read.header), website=agreement.supplier_website,
            name=agreement.supplier_name,
        )
    added = replace_drafts(session, agreement, read.terms, suggest_for(session,
                                                                        agreement.company_id))
    agreement.status = AgreementStatus.REVIEW.value
    agreement.read_error = None
    agreement.read_at = datetime.now(timezone.utc)
    session.add(agreement)
    session.flush()
    settle_status(session, agreement)
    logger.info("agreement %s: %d draft term(s) from %d page(s), %d dropped, %d unread",
                agreement.id, added, read.pages, read.dropped_terms, read.failed_pages)


def _fail(session: Session, agreement_id: str, error: str) -> None:
    agreement = session.get(Agreement, agreement_id)
    agreement.read_error = error
    agreement.status = (AgreementStatus.FAILED.value
                        if agreement.read_attempts >= config.AGREEMENT_MAX_ATTEMPTS
                        else AgreementStatus.PENDING.value)
    session.add(agreement)
    session.commit()
    logger.warning("agreement %s: %s", agreement_id, error)
