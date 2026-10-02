"""A company with suppliers, invoice lines and an active agreement, for compliance tests."""
from __future__ import annotations

import json
import math
import re
from datetime import date
from decimal import Decimal

from qdrant_client import QdrantClient
from sqlmodel import Session

from ai_api.items.index import ItemIndex

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
    SpendCategory,
    SpendTree,
    Vendor,
)

_PURCHASES = re.compile(r"^Purchase (\d+):\n(.*?)(?=\n\n)", re.M | re.S)

WORDS = ["laptop", "thinkpad", "dell", "monitor", "dock", "coffee", "sleeve", "cable",
         "equipment", "office"]


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

    def tree(self, *names: str) -> dict[str, SpendCategory]:
        """A spend tree for the company with one top-level category per name."""
        tree = SpendTree(organization_id=self.company.organization_id, name="Acme tree")
        self.session.add(tree)
        self.session.commit()
        categories = {name: SpendCategory(spend_tree_id=tree.id, name=name, level_1=name)
                      for name in names}
        self.session.add_all(categories.values())
        self.company.spend_tree_id = tree.id
        self.session.add(self.company)
        self.session.commit()
        return categories

    def vendor(self, name: str, vat: str) -> Vendor:
        vendor = Vendor(name=name, vat_number=vat, country_code="DK")
        self.session.add(vendor)
        self.session.commit()
        return vendor

    def line(self, vendor: Vendor, item: str, *, quantity: str = "1", unit_price: str,
             amount: str | None = None, discount: str | None = None, unit: str = "unit",
             on: date = date(2026, 3, 1), invoice: Invoice | None = None,
             category: SpendCategory | None = None) -> InvoiceLine:
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
                           spend_category_id=category.id if category else None,
                           level_1=category.name if category else None,
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
    """In scope when a purchase names one of the words; the priced item when it names `item`.
    Answers a numbered batch by number, and counts every prompt it is asked."""

    def __init__(self, scope_words: tuple[str, ...], item: str | None = None,
                 per_box: bool = False) -> None:
        self.scope_words = scope_words
        self.item = item
        self.per_box = per_box
        self.questions = 0

    def __call__(self, prompt: str) -> str:
        self.questions += 1
        numbered = _PURCHASES.findall(prompt)
        if numbered:
            return json.dumps({"answers": [{"n": int(number), **self._answer(text)}
                                           for number, text in numbered]})
        return json.dumps(self._answer(prompt.split("Purchase:", 1)[1]))

    def _answer(self, purchase: str) -> dict:
        text = purchase.split("\n\n", 1)[0].lower()
        return {"in_scope": any(word in text for word in self.scope_words),
                "same_item": bool(self.item and self.item.lower() in text),
                "units_comparable": not self.per_box, "confidence": 0.9,
                "reason": "Judged by the stub."}


def item_index() -> ItemIndex:
    """An in-memory item index over the bag-of-words embedder."""
    return ItemIndex(QdrantClient(location=":memory:"), embed)
