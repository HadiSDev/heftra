"""Writing a run's findings over the last run's, keeping every review."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlalchemy import delete
from sqlmodel import Session, col, select

from web_api.db.models import Agreement, AgreementFinding, FindingReviewStatus

from .drafts import FindingDraft


def store_findings(session: Session, agreement: Agreement, term_ids: list[str],
                   drafts: list[FindingDraft], base_currency: str | None) -> None:
    """Upsert by (term, line, kind), delete what wasn't produced again, except not-in-scope rulings."""
    now = datetime.now(timezone.utc)
    existing = {
        (finding.term_id, finding.invoice_line_id, finding.kind): finding
        for finding in session.exec(
            select(AgreementFinding).where(AgreementFinding.agreement_id == agreement.id)
        ).all()
    }
    produced: set[tuple[str, str, str]] = set()
    for draft in drafts:
        key = (draft.term_id, draft.line.line_id, draft.kind.value)
        produced.add(key)
        finding = existing.get(key) or AgreementFinding(
            company_id=agreement.company_id, agreement_id=agreement.id, term_id=draft.term_id,
            invoice_line_id=draft.line.line_id, invoice_id=draft.line.invoice_id,
            kind=draft.kind.value, severity=draft.severity.value, amount=draft.amount,
            line_amount=draft.line.base_amount, from_supplier=draft.from_supplier,
            reason=draft.reason, computed_at=now,
        )
        finding.vendor_id = draft.line.vendor_id
        finding.severity = draft.severity.value
        finding.amount = draft.amount
        finding.line_amount = draft.line.base_amount
        finding.from_supplier = draft.from_supplier
        finding.currency = base_currency
        finding.expected = draft.expected
        finding.actual = draft.actual
        finding.quantity = draft.line.quantity
        finding.reason = draft.reason
        finding.judge_confidence = draft.confidence
        finding.spent_on = draft.line.spent_on
        finding.computed_at = now
        session.add(finding)
    for key, finding in existing.items():
        if key in produced:
            continue
        ruled_out = finding.review_status == FindingReviewStatus.NOT_IN_SCOPE.value
        if not ruled_out or finding.term_id not in term_ids:
            session.delete(finding)
    session.flush()


def delete_undecided_findings(session: Session, agreement_ids: list[str],
                              confirmed_term_ids: list[str]) -> None:
    """Findings of terms that are no longer confirmed go."""
    session.exec(delete(AgreementFinding).where(
        col(AgreementFinding.agreement_id).in_(agreement_ids),
        col(AgreementFinding.term_id).not_in(confirmed_term_ids),
    ))
