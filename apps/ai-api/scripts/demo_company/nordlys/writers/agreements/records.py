"""The agreements as read, confirmed and analysed: their files, terms, findings and the terms'
monthly spend."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from decimal import Decimal

from sqlmodel import Session

from web_api.agreements.constants import AGREEMENT_FILE_TYPE
from web_api.db.models import (
    Agreement,
    AgreementFinding,
    AgreementStatus,
    AgreementTerm,
    AgreementTermSpend,
    AgreementTermStatus,
    File,
    FindingReviewStatus,
)

from ...catalog.shapes import AgreementSpec, SupplierSpec, TermSpec
from ...catalog.suppliers import by_key
from ...documents.agreement_pdf import agreement_pdf
from ...generation.planned import PlannedInvoice
from ...ids import COMPANY_ID, demo_id
from ...settings import CURRENCY
from ..ledger.books import Books, invoice_id, line_id
from .rules import OFF_CONTRACT, judge
from .scope import ScopedLine, scoped_lines

SEVERITIES = {
    "off_contract": "rule_break",
    "overcharge": "rule_break",
    "missed_discount": "warning",
    "price_unverifiable": "warning",
    "potential_saving": "info",
    "compliant": "info",
}
JUDGE_CONFIDENCE = Decimal("0.93")
EXCEPTIONS = 2
EXCEPTION_NOTE = ("Approved by the site manager: the agreed supplier could not deliver in time, "
                  "so the order went to the nearest supplier.")
UPLOADED_AT = time(10, 15)


@dataclass
class AgreementOutcome:
    findings: int = 0
    by_kind: dict[str, int] = field(default_factory=lambda: defaultdict(int))
    files: dict[str, bytes] = field(default_factory=dict)


class AgreementWriter:
    def __init__(self, session: Session, books: Books, plan: list[PlannedInvoice],
                 uploader: str, now: datetime) -> None:
        self._session = session
        self._books = books
        self._plan = plan
        self._uploader = uploader
        self._now = now
        self._suppliers = by_key()

    def write(self, agreements: tuple[AgreementSpec, ...]) -> AgreementOutcome:
        """Add the agreements with everything recorded against them; the caller commits and
        stores the returned PDFs under their keys."""
        outcome = AgreementOutcome()
        for spec in agreements:
            self._agreement(spec, outcome)
        self._session.flush()
        return outcome

    def _agreement(self, spec: AgreementSpec, outcome: AgreementOutcome) -> None:
        supplier = self._suppliers[spec.supplier]
        agreement_id = demo_id("agreement", spec.key)
        uploaded = datetime.combine(spec.uploaded_on, UPLOADED_AT, tzinfo=timezone.utc)
        pdf = agreement_pdf(spec.title, spec.pages)
        key = (f"companies/{COMPANY_ID}/agreements/{agreement_id}/"
               f"{demo_id('agreement-file', spec.key).replace('-', '')}.pdf")
        outcome.files[key] = pdf
        file_row = File(id=demo_id("file", spec.key), company_id=COMPANY_ID,
                        uploaded_by=self._uploader, filename=spec.filename,
                        file_type=AGREEMENT_FILE_TYPE, storage_path=key, file_size=len(pdf),
                        created_at=uploaded)
        self._session.add(file_row)
        self._session.flush()
        agreement = Agreement(
            id=agreement_id, company_id=COMPANY_ID, file_id=file_row.id, title=spec.title,
            reference=spec.reference, vendor_id=self._books.vendors[spec.supplier].id,
            supplier_name=supplier.name, supplier_vat_number=supplier.vat_number,
            supplier_website=supplier.website, starts_on=spec.starts_on, ends_on=spec.ends_on,
            currency=CURRENCY, summary=spec.summary, status=AgreementStatus.ACTIVE.value,
            read_attempts=1, read_started_at=uploaded, read_at=uploaded + timedelta(minutes=2),
            analysed_at=self._now, full_analysis=False, uploaded_by=self._uploader,
            created_at=uploaded)
        self._session.add(agreement)
        self._session.flush()
        for term_spec in spec.terms:
            term = self._term(spec, term_spec, uploaded)
            scoped = scoped_lines(self._plan, spec, term_spec)
            self._findings(agreement, term, term_spec, scoped, supplier, outcome)
            self._term_spend(term, scoped)

    def _term(self, spec: AgreementSpec, term: TermSpec, uploaded: datetime) -> AgreementTerm:
        row = AgreementTerm(
            id=demo_id("agreement-term", f"{spec.key}:{term.key}"),
            agreement_id=demo_id("agreement", spec.key), kind=term.kind,
            status=AgreementTermStatus.CONFIRMED.value, source="ai", scope=term.scope,
            item=term.item, unit=term.unit, unit_price=term.unit_price,
            discount_percent=term.discount_percent, commitment_amount=term.commitment_amount,
            commitment_period=term.commitment_period,
            tiers=list(term.tiers) if term.tiers else None, currency=CURRENCY,
            scope_category_ids=[self._books.leaves[code].id for code in term.leaves],
            quotes=[{"text": term.quote, "page": term.page}], confidence=term.confidence,
            created_at=uploaded + timedelta(minutes=2), updated_at=uploaded + timedelta(hours=3))
        self._session.add(row)
        self._session.flush()
        return row

    def _findings(self, agreement: Agreement, term: AgreementTerm, spec: TermSpec,
                  scoped: list[ScopedLine], supplier: SupplierSpec,
                  outcome: AgreementOutcome) -> None:
        exceptions = 0
        for entry in scoped:
            verdict = judge(spec, entry, supplier.name)
            if verdict is None:
                continue
            finding = AgreementFinding(
                id=demo_id("finding", f"{term.id}:{line_id(entry.invoice, entry.line)}"),
                company_id=COMPANY_ID, agreement_id=agreement.id, term_id=term.id,
                invoice_line_id=line_id(entry.invoice, entry.line),
                invoice_id=invoice_id(entry.invoice),
                vendor_id=self._books.vendors[entry.invoice.supplier.key].id, kind=verdict.kind,
                severity=SEVERITIES[verdict.kind], amount=verdict.amount,
                line_amount=entry.line.amount, from_supplier=entry.from_supplier,
                currency=CURRENCY, expected=verdict.expected, actual=verdict.actual,
                quantity=entry.line.quantity, reason=verdict.reason,
                judge_confidence=JUDGE_CONFIDENCE, spent_on=entry.invoice.on,
                computed_at=self._now)
            if verdict.kind == OFF_CONTRACT and exceptions < EXCEPTIONS:
                self._excepted(finding, entry.invoice.on)
                exceptions += 1
            self._session.add(finding)
            outcome.findings += 1
            outcome.by_kind[verdict.kind] += 1

    def _excepted(self, finding: AgreementFinding, spent_on: date) -> None:
        finding.review_status = FindingReviewStatus.EXCEPTION.value
        finding.review_note = EXCEPTION_NOTE
        finding.reviewed_by = self._uploader
        finding.reviewed_at = datetime.combine(spent_on + timedelta(days=9), UPLOADED_AT,
                                               tzinfo=timezone.utc)

    def _term_spend(self, term: AgreementTerm, scoped: list[ScopedLine]) -> None:
        totals: dict[tuple[date, bool], list] = defaultdict(lambda: [Decimal(0), 0])
        for entry in scoped:
            month = entry.invoice.on.replace(day=1)
            totals[(month, entry.from_supplier)][0] += entry.line.amount
            totals[(month, entry.from_supplier)][1] += 1
        for (month, from_supplier), (amount, lines) in sorted(totals.items()):
            self._session.add(AgreementTermSpend(
                id=demo_id("term-spend", f"{term.id}:{month.isoformat()}:{from_supplier}"),
                term_id=term.id, month=month, from_supplier=from_supplier, amount=amount,
                lines=lines))
