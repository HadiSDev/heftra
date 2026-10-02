"""Writing a page of a term's findings over the last run's, keeping every review."""
from __future__ import annotations

from collections import Counter
from collections.abc import Callable
from datetime import datetime, timezone

from sqlalchemy import and_, delete, exists
from sqlmodel import Session, col, select

from web_api.db.models import (
    Agreement,
    AgreementFinding,
    AgreementScopeJudgement,
    FindingReviewStatus,
    Invoice,
    InvoiceLine,
)

from .drafts import FindingDraft
from .lines import AnalysedLine, invoice_discount_rates
from .rules import ConvertPrice, TermContext, evaluate

FromSupplier = Callable[[AnalysedLine], bool]


def write_page(session: Session, agreement: Agreement, context: TermContext,
               page: list[tuple[AnalysedLine, AgreementScopeJudgement]], *,
               from_supplier: FromSupplier, convert: ConvertPrice,
               base_currency: str | None) -> Counter[str]:
    """Upsert the page's findings by (term, line, kind), delete what its lines no longer give,
    and commit; returns the findings written by kind."""
    discounts = invoice_discount_rates(session, {line.invoice_id for line, _ in page})
    drafts = [draft for line, judgement in page
              for draft in evaluate(context, line, judgement, from_supplier(line),
                                    convert=convert,
                                    invoice_discount=discounts.get(line.invoice_id))]
    line_ids = [line.line_id for line, _ in page]
    existing = {
        (finding.invoice_line_id, finding.kind): finding
        for finding in session.exec(
            select(AgreementFinding).where(
                AgreementFinding.term_id == context.term.id,
                col(AgreementFinding.invoice_line_id).in_(line_ids),
            )
        ).all()
    }
    now = datetime.now(timezone.utc)
    produced: set[tuple[str, str]] = set()
    for draft in drafts:
        key = (draft.line.line_id, draft.kind.value)
        produced.add(key)
        session.add(_upserted(existing.get(key), agreement, draft, base_currency, now))
    for key, finding in existing.items():
        if key not in produced and finding.review_status != FindingReviewStatus.NOT_IN_SCOPE.value:
            session.delete(finding)
    session.commit()
    return Counter(draft.kind.value for draft in drafts)


def prune_out_of_scope(session: Session, term_id: str, term_key: str) -> None:
    """Delete the term's findings whose line's item isn't judged in scope under `term_key`,
    keeping not-in-scope rulings; commits."""
    in_scope = exists().where(
        InvoiceLine.id == AgreementFinding.invoice_line_id,
        exists().where(and_(
            AgreementScopeJudgement.question_key == InvoiceLine.item_key,
            AgreementScopeJudgement.term_id == term_id,
            AgreementScopeJudgement.term_key == term_key,
            AgreementScopeJudgement.in_scope == True,  # noqa: E712
        )),
    )
    session.exec(delete(AgreementFinding).where(
        AgreementFinding.term_id == term_id,
        AgreementFinding.review_status != FindingReviewStatus.NOT_IN_SCOPE.value,
        ~in_scope,
    ))
    session.commit()


def prune_outside_validity(session: Session, agreement: Agreement) -> None:
    """Delete the agreement's findings on lines invoiced outside its validity; commits."""
    outside = Invoice.invoice_date < agreement.starts_on
    if agreement.ends_on is not None:
        outside = outside | (Invoice.invoice_date > agreement.ends_on)
    session.exec(delete(AgreementFinding).where(
        AgreementFinding.agreement_id == agreement.id,
        col(AgreementFinding.invoice_id).in_(
            select(Invoice.id).where(Invoice.company_id == agreement.company_id, outside)),
    ))
    session.commit()


def _upserted(finding: AgreementFinding | None, agreement: Agreement, draft: FindingDraft,
              base_currency: str | None, now: datetime) -> AgreementFinding:
    finding = finding or AgreementFinding(
        company_id=agreement.company_id, agreement_id=agreement.id, term_id=draft.term_id,
        invoice_line_id=draft.line.line_id, invoice_id=draft.line.invoice_id,
        kind=draft.kind.value, severity=draft.severity.value, amount=draft.amount,
        line_amount=draft.line.base_amount, from_supplier=draft.from_supplier,
        reason=draft.reason, computed_at=now,
    )
    finding.invoice_id = draft.line.invoice_id
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
    return finding


def delete_undecided_findings(session: Session, agreement_ids: list[str],
                              confirmed_term_ids: list[str]) -> None:
    """Findings of terms that are no longer confirmed go."""
    session.exec(delete(AgreementFinding).where(
        col(AgreementFinding.agreement_id).in_(agreement_ids),
        col(AgreementFinding.term_id).not_in(confirmed_term_ids),
    ))
