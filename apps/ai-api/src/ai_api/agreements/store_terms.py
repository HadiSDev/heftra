"""Replacing an agreement's draft terms with a new reading's, keeping decided ones."""
from __future__ import annotations

from sqlalchemy import delete
from sqlmodel import Session, select

from web_api.db.models import (
    Agreement,
    AgreementTerm,
    AgreementTermSource,
    AgreementTermStatus,
)

from .scope_categories import Suggest
from .terms import DraftTerm, comparable


def replace_drafts(session: Session, agreement: Agreement, drafts: list[DraftTerm],
                   suggest: Suggest) -> int:
    """Delete the drafts, add the new ones not already decided on; returns how many were added."""
    session.exec(delete(AgreementTerm).where(
        AgreementTerm.agreement_id == agreement.id,
        AgreementTerm.status == AgreementTermStatus.DRAFT.value,
    ))
    decided = {
        (term.kind, comparable(term.item or term.scope))
        for term in session.exec(
            select(AgreementTerm).where(AgreementTerm.agreement_id == agreement.id)
        ).all()
    }
    added = 0
    for draft in drafts:
        if (draft.kind, comparable(draft.item or draft.scope)) in decided:
            continue
        session.add(AgreementTerm(
            agreement_id=agreement.id,
            kind=draft.kind,
            status=AgreementTermStatus.DRAFT.value,
            source=AgreementTermSource.AI.value,
            scope=draft.scope,
            conditions=draft.conditions,
            item=draft.item,
            unit=draft.unit,
            unit_price=draft.unit_price,
            discount_percent=draft.discount_percent,
            commitment_amount=draft.commitment_amount,
            commitment_period=draft.commitment_period,
            tiers=draft.tiers or None,
            currency=draft.currency or agreement.currency,
            scope_category_ids=suggest(draft.item or draft.scope),
            quotes=draft.quotes,
            confidence=draft.confidence,
        ))
        added += 1
    return added
