"""A company with suppliers, invoice lines and an active agreement, for compliance tests."""
from __future__ import annotations

import json
import math
from datetime import date
from decimal import Decimal

from sqlmodel import Session

from web_api.db.models import (
    Agreement,
    AgreementStatus,
    AgreementTerm,
    AgreementTermKind,
    AgreementTermStatus,
    Company,
    File,
    Invoice,
    InvoiceLine,
    Organization,
    Vendor,
)

WORDS = ["laptop", "thinkpad", "dell", "monitor", "dock", "coffee", "sleeve", "cable"]


def embed(texts: list[str]) -> list[list[float]]:
    """A bag of known words, normalised, so similarity is predictable."""
    vectors = []
    for text in texts:
        lowered = text.lower()
        vector = [1.0 if word in lowered else 0.0 for word in WORDS] + [0.1]
        norm = math.sqrt(sum(value * value for value in vector))
        vectors.append([value / norm for value in vector])
    return vectors


class Books:
    def __init__(self, session: Session) -> None:
        self.session = session
        org = Organization(name="Acme Org", clerk_org_id="clerk_acme")
        session.add(org)
        session.commit()
        self.company = Company(organization_id=org.id, name="Acme", base_currency="DKK")
        session.add(self.company)
        session.commit()
        self.atea = self.vendor("Atea A/S", "DK12345678")
        self.proshop = self.vendor("Proshop A/S", "DK87654321")

    def vendor(self, name: str, vat: str) -> Vendor:
        vendor = Vendor(name=name, vat_number=vat, country_code="DK")
        self.session.add(vendor)
        self.session.commit()
        return vendor

    def line(self, vendor: Vendor, item: str, *, quantity: str = "1", unit_price: str,
             amount: str | None = None, discount: str | None = None, unit: str = "unit",
             on: date = date(2026, 3, 1), invoice: Invoice | None = None) -> InvoiceLine:
        if invoice is None:
            invoice = Invoice(company_id=self.company.id, vendor_id=vendor.id,
                              invoice_number=f"{vendor.name}-{item}", invoice_date=on,
                              currency="DKK", status="posted")
            self.session.add(invoice)
            self.session.commit()
        total = Decimal(amount) if amount else Decimal(quantity) * Decimal(unit_price)
        line = InvoiceLine(company_id=self.company.id, invoice_id=invoice.id, item_name=item,
                           quantity=Decimal(quantity), unit=unit, unit_price=Decimal(unit_price),
                           amount=total, base_amount=total,
                           discount=Decimal(discount) if discount else None,
                           status="ai_categorized", sequence=0)
        self.session.add(line)
        self.session.commit()
        return line

    def agreement(self, *, starts_on: date = date(2026, 1, 1)) -> Agreement:
        file_row = File(company_id=self.company.id, filename="atea.pdf",
                        file_type="agreement_pdf", storage_path="k")
        self.session.add(file_row)
        self.session.commit()
        agreement = Agreement(company_id=self.company.id, file_id=file_row.id, title="Atea",
                              vendor_id=self.atea.id, starts_on=starts_on, currency="DKK",
                              status=AgreementStatus.ACTIVE.value, uploaded_by="user-1")
        self.session.add(agreement)
        self.session.commit()
        return agreement

    def term(self, agreement: Agreement, kind: AgreementTermKind, scope: str,
             **fields) -> AgreementTerm:
        term = AgreementTerm(agreement_id=agreement.id, kind=kind.value,
                             status=AgreementTermStatus.CONFIRMED.value, scope=scope,
                             currency="DKK", **fields)
        self.session.add(term)
        self.session.commit()
        return term


class Judge:
    """In scope when the line names one of the words; the priced item when it names `item`."""

    def __init__(self, scope_words: tuple[str, ...], item: str | None = None,
                 per_box: bool = False) -> None:
        self.scope_words = scope_words
        self.item = item
        self.per_box = per_box
        self.questions = 0

    def __call__(self, prompt: str) -> str:
        self.questions += 1
        line = prompt.split("Invoice line:")[1].lower()
        in_scope = any(word in line for word in self.scope_words)
        same = bool(self.item and self.item.lower() in line)
        return json.dumps({"in_scope": in_scope, "same_item": same,
                           "units_comparable": not self.per_box, "confidence": 0.9,
                           "reason": "Judged by the stub."})
