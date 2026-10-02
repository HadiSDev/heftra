"""A term's in-scope lines, read a page at a time with the judgement of the item each bought."""
from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass
from datetime import date, datetime

from sqlalchemy import and_, exists, func, or_, tuple_
from sqlmodel import Session, col, select

from web_api.db.models import (
    AgreementFinding,
    AgreementScopeJudgement,
    FindingReviewStatus,
    Invoice,
    InvoiceLine,
    Vendor,
)
from web_api.vat import international_vat

from .. import config
from .lines import AnalysedLine


@dataclass(frozen=True)
class TermLines:
    """Which lines of a term to read: its judgements under `term_key`, within the dates,
    changed after `since` when it is set."""

    company_id: str
    term_id: str
    term_key: str
    start: date
    end: date | None
    since: datetime | None


def in_scope_pages(session: Session, wanted: TermLines, *, page_size: int | None = None
                   ) -> Iterator[list[tuple[AnalysedLine, AgreementScopeJudgement]]]:
    """Pages of the term's in-scope lines in invoice date order, leaving out lines ruled out."""
    size = page_size or config.AGREEMENT_PAGE_SIZE
    after: tuple[date, str] | None = None
    while True:
        statement = _statement(wanted).limit(size)
        if after is not None:
            statement = statement.where(tuple_(Invoice.invoice_date, InvoiceLine.id) > after)
        rows = session.exec(statement).all()
        if not rows:
            return
        yield [(_line(row), row[1]) for row in rows]
        last = rows[-1]
        after = (last[2], last[0].id)


def _statement(wanted: TermLines):
    ruled_out = exists().where(
        AgreementFinding.term_id == wanted.term_id,
        AgreementFinding.invoice_line_id == InvoiceLine.id,
        AgreementFinding.review_status == FindingReviewStatus.NOT_IN_SCOPE.value,
    )
    base = func.coalesce(InvoiceLine.base_amount, InvoiceLine.amount)
    statement = (
        select(InvoiceLine, AgreementScopeJudgement, Invoice.invoice_date, Invoice.currency,
               Invoice.vendor_id, Vendor.name, Vendor.vat_number, Vendor.country_code)
        .join(Invoice, Invoice.id == InvoiceLine.invoice_id)
        .outerjoin(Vendor, Vendor.id == Invoice.vendor_id)
        .join(AgreementScopeJudgement, and_(
            AgreementScopeJudgement.question_key == InvoiceLine.item_key,
            AgreementScopeJudgement.term_id == wanted.term_id,
            AgreementScopeJudgement.term_key == wanted.term_key,
            AgreementScopeJudgement.in_scope == True,  # noqa: E712
        ))
        .where(InvoiceLine.company_id == wanted.company_id,
               Invoice.invoice_date >= wanted.start, base > 0, ~ruled_out)
        .order_by(col(Invoice.invoice_date), col(InvoiceLine.id))
    )
    if wanted.end is not None:
        statement = statement.where(Invoice.invoice_date <= wanted.end)
    if wanted.since is not None:
        statement = statement.where(or_(col(InvoiceLine.changed_at) > wanted.since,
                                        col(Invoice.changed_at) > wanted.since))
    return statement


def _line(row) -> AnalysedLine:
    line, _, spent_on, currency, vendor_id, vendor_name, vat, country = row
    base = line.base_amount if line.base_amount is not None else line.amount
    return AnalysedLine(
        line_id=line.id, invoice_id=line.invoice_id, vendor_id=vendor_id,
        vendor_name=vendor_name, vendor_vat=international_vat(vat, country),
        item_name=line.item_name, description=line.description, quantity=line.quantity,
        unit=line.unit, unit_price=line.unit_price, amount=line.amount,
        discount=line.discount, base_amount=base, currency=currency, spent_on=spent_on,
        category_id=line.spend_category_id,
        category_path=tuple(level for level in (line.level_1, line.level_2, line.level_3,
                                                line.level_4) if level),
    )
