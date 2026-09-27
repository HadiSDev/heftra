"""A person adding, correcting, confirming or rejecting an agreement's terms."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete
from sqlmodel import Session

from ..audit import diff_changes, record_audit
from ..db.models import (
    Agreement,
    AgreementFinding,
    AgreementScopeJudgement,
    AgreementTerm,
    AgreementTermSource,
    AgreementTermStatus,
)
from ..schemas.agreements import TermCreate, TermPatch
from .analysis import request_analysis
from .constants import AUDIT_TERM
from .status import settle_status

JUDGED_FIELDS = ("scope", "conditions", "item", "unit")

TERM_AUDIT_FIELDS = (
    "status", "scope", "conditions", "item", "unit", "unit_price", "discount_percent",
    "commitment_amount", "commitment_period", "tiers", "currency", "scope_category_ids",
)


def add_term(session: Session, agreement: Agreement, body: TermCreate, actor: str) -> AgreementTerm:
    """A term a person wrote, confirmed from the start."""
    term = AgreementTerm(
        agreement_id=agreement.id,
        kind=body.kind.value,
        status=AgreementTermStatus.CONFIRMED.value,
        source=AgreementTermSource.HUMAN.value,
        scope=body.scope,
        conditions=body.conditions,
        item=body.item,
        unit=body.unit,
        unit_price=body.unit_price,
        discount_percent=body.discount_percent,
        commitment_amount=body.commitment_amount,
        commitment_period=body.commitment_period,
        tiers=[tier.model_dump(mode="json") for tier in body.tiers] if body.tiers else None,
        currency=_currency(body.currency, agreement.currency),
        scope_category_ids=body.scope_category_ids,
    )
    session.add(term)
    session.flush()
    record_audit(session, entity_type=AUDIT_TERM, entity_id=term.id, action="create", actor=actor,
                 changes=diff_changes({}, _audited(term), TERM_AUDIT_FIELDS))
    settle_status(session, agreement)
    request_analysis(session, agreement.company_id, actor)
    return term


def patch_term(session: Session, agreement: Agreement, term: AgreementTerm, body: TermPatch,
               actor: str) -> AgreementTerm:
    """Apply the fields sent; judged fields changing forget the term's scope judgements."""
    before = _audited(term)
    was_confirmed = term.status == AgreementTermStatus.CONFIRMED.value
    sent = body.model_fields_set
    for field in sent:
        value = getattr(body, field)
        if field == "status":
            value = value.value if value is not None else term.status
        elif field == "tiers" and value is not None:
            value = [tier.model_dump(mode="json") for tier in value]
        setattr(term, field, value)
    term.updated_at = datetime.now(timezone.utc)
    session.add(term)

    changes = diff_changes(before, _audited(term), TERM_AUDIT_FIELDS)
    if not changes:
        return term
    record_audit(session, entity_type=AUDIT_TERM, entity_id=term.id, action="update",
                 actor=actor, changes=changes)
    changed = {change["field"] for change in changes}
    if changed & set(JUDGED_FIELDS):
        session.exec(delete(AgreementScopeJudgement)
                     .where(AgreementScopeJudgement.term_id == term.id))
    if term.status == AgreementTermStatus.REJECTED.value:
        session.exec(delete(AgreementFinding).where(AgreementFinding.term_id == term.id))
    settle_status(session, agreement)
    if was_confirmed or term.status == AgreementTermStatus.CONFIRMED.value:
        request_analysis(session, agreement.company_id, actor)
    return term


def _audited(term: AgreementTerm) -> dict:
    return {field: getattr(term, field) for field in TERM_AUDIT_FIELDS}


def _currency(sent: str | None, agreement_currency: str | None) -> str | None:
    chosen = sent or agreement_currency
    return chosen.upper() if chosen else None
