"""Agreements, terms and findings written straight into the database for tests."""
from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal

from sqlmodel import Session

from web_api.db.models import (
    Agreement,
    AgreementFinding,
    AgreementStatus,
    AgreementTerm,
    AgreementTermSpend,
    AgreementTermKind,
    AgreementTermStatus,
    File,
    FindingKind,
    FindingSeverity,
    Vendor,
)

SEVERITIES = {
    FindingKind.OFF_CONTRACT: FindingSeverity.RULE_BREAK,
    FindingKind.OVERCHARGE: FindingSeverity.RULE_BREAK,
    FindingKind.MISSED_DISCOUNT: FindingSeverity.WARNING,
    FindingKind.PRICE_UNVERIFIABLE: FindingSeverity.WARNING,
    FindingKind.POTENTIAL_SAVING: FindingSeverity.INFO,
    FindingKind.COMPLIANT: FindingSeverity.INFO,
}


def supplier(session: Session, name: str = "Atea A/S", vat: str = "DK12345678") -> Vendor:
    vendor = Vendor(name=name, vat_number=vat, country_code="DK")
    session.add(vendor)
    session.commit()
    session.refresh(vendor)
    return vendor


def agreement(session: Session, company_id: str, *, vendor: Vendor | None = None,
              status: AgreementStatus = AgreementStatus.ACTIVE, uploaded_by: str = "user-1",
              starts_on: date | None = date(2025, 1, 1), ends_on: date | None = None,
              key: str = "companies/x/agreements/y/file.pdf") -> Agreement:
    file_row = File(company_id=company_id, filename="Atea framework.pdf",
                    file_type="agreement_pdf", storage_path=key, file_size=1000)
    session.add(file_row)
    session.commit()
    record = Agreement(company_id=company_id, file_id=file_row.id, title="Atea framework",
                       vendor_id=vendor.id if vendor else None, starts_on=starts_on,
                       ends_on=ends_on, currency="DKK", status=status.value,
                       uploaded_by=uploaded_by)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def term(session: Session, agreement_id: str, *,
         kind: AgreementTermKind = AgreementTermKind.PREFERRED_SUPPLIER,
         status: AgreementTermStatus = AgreementTermStatus.CONFIRMED,
         scope: str = "IT equipment", **fields) -> AgreementTerm:
    record = AgreementTerm(agreement_id=agreement_id, kind=kind.value, status=status.value,
                           scope=scope, quotes=[{"text": "IT equipment from Atea", "page": 3}],
                           **fields)
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def finding(session: Session, *, agreement: Agreement, term: AgreementTerm, line_id: str,
            invoice_id: str, kind: FindingKind = FindingKind.OFF_CONTRACT,
            amount: str = "100.00", line_amount: str | None = None,
            from_supplier: bool = False, vendor_id: str | None = None,
            spent_on: date = date(2025, 7, 1)) -> AgreementFinding:
    record = AgreementFinding(
        company_id=agreement.company_id, agreement_id=agreement.id, term_id=term.id,
        invoice_line_id=line_id, invoice_id=invoice_id, vendor_id=vendor_id,
        kind=kind.value, severity=SEVERITIES[kind].value, amount=Decimal(amount),
        line_amount=Decimal(line_amount or amount), from_supplier=from_supplier,
        currency="DKK", reason="Bought elsewhere.", spent_on=spent_on,
        computed_at=datetime.now(timezone.utc),
    )
    session.add(record)
    session.commit()
    session.refresh(record)
    return record


def term_spend(session: Session, term: AgreementTerm, month: date, amount: str, *,
               from_supplier: bool, lines: int = 1) -> AgreementTermSpend:
    row = AgreementTermSpend(term_id=term.id, month=month, from_supplier=from_supplier,
                             amount=Decimal(amount), lines=lines)
    session.add(row)
    session.commit()
    return row
