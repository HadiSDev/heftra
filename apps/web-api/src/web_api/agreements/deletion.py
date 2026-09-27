"""Removing agreements and everything recorded against them."""
from __future__ import annotations

from collections.abc import Collection

from sqlalchemy import delete
from sqlmodel import Session, col, select

from ..db.models import (
    Agreement,
    AgreementFinding,
    AgreementScopeJudgement,
    AgreementTerm,
    File,
)


def delete_agreements(session: Session, agreement_ids: Collection[str]) -> list[str]:
    """Delete the agreements, their terms, findings, judgements and file rows.

    Returns the storage keys of their files, for the caller to remove once it has committed.
    """
    if not agreement_ids:
        return []
    ids = list(agreement_ids)
    file_ids = list(session.exec(
        select(Agreement.file_id).where(col(Agreement.id).in_(ids))
    ).all())
    keys = list(session.exec(
        select(File.storage_path).where(col(File.id).in_(file_ids))
    ).all())
    term_ids = select(AgreementTerm.id).where(col(AgreementTerm.agreement_id).in_(ids))
    session.exec(delete(AgreementScopeJudgement)
                 .where(col(AgreementScopeJudgement.term_id).in_(term_ids)))
    session.exec(delete(AgreementFinding).where(col(AgreementFinding.agreement_id).in_(ids)))
    session.exec(delete(AgreementTerm).where(col(AgreementTerm.agreement_id).in_(ids)))
    session.exec(delete(Agreement).where(col(Agreement.id).in_(ids)))
    session.exec(delete(File).where(col(File.id).in_(file_ids)))
    return [key for key in keys if key]


def delete_company_agreements(session: Session, company_id: str) -> list[str]:
    ids = session.exec(select(Agreement.id).where(Agreement.company_id == company_id)).all()
    return delete_agreements(session, ids)
