"""A deterministic synthetic company with many lines, varied items and one IT framework agreement."""
from __future__ import annotations

import random
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from faker import Faker
from sqlalchemy import insert
from sqlmodel import Session, select

from ai_api.rag.indexer import load_accounts
from ai_api.synthdata.catalog import line_descriptions, vendor_name
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
    Vendor,
)
from web_api.spend_trees.service import ensure_default_tree, node_path

SUPPLIER = ("CS-Online A/S", "DK20366532")
WEBSHOPS = 5
VENDORS = 40
LINES_PER_INVOICE = 4
CHUNK = 20_000
LAST_DAY = date(2026, 9, 30)
DAYS = 3 * 365
IT_ITEMS = [
    "Lenovo ThinkPad T14 Gen 5 laptop", "Dell Latitude 5450 laptop", "Apple MacBook Pro 14 M5",
    "Magic Keyboard Touch ID DK", "Logitech MX Master 3S mouse", "Apple Magic Trackpad",
    "Dell 27 USB-C hub monitor P2725HE", "Seagate Exos 10TB NAS drive", "SanDisk Extreme PRO 256GB",
    "Apple 96W USB-C power adapter", "Jabra Evolve2 65 headset", "Logitech C920 webcam",
    "CalDigit TS4 docking station", "USB-C to HDMI cable 2m", "Samsung T7 1TB SSD",
]


@dataclass(frozen=True)
class Item:
    name: str
    category: SpendCategory
    vendor_index: int
    unit_price: Decimal


@dataclass(frozen=True)
class Dataset:
    company_id: str
    agreement_id: str
    items: int


def build(session: Session, *, lines: int, items: int, seed: int) -> Dataset:
    """Create the company, its suppliers, items, lines and agreement; returns their ids."""
    rng = random.Random(seed)
    faker = Faker()
    faker.seed_instance(seed)
    org = Organization(name="Bench Org", clerk_org_id=f"bench-{seed}")
    session.add(org)
    session.commit()
    tree = ensure_default_tree(session, org.id)
    company = Company(organization_id=org.id, name="Bench ApS", base_currency="DKK",
                      spend_tree_id=tree.id, description="A software and data consultancy.")
    session.add(company)
    session.commit()
    leaves = _leaves(session, tree.id)
    it_leaf = next((leaf for leaf in leaves if "equipment" in leaf.name.lower()), leaves[0])
    vendor_ids = _vendors(session, rng, faker)
    catalog = _items(rng, faker, items, leaves, it_leaf)
    _lines(session, company.id, catalog, vendor_ids, lines, rng)
    agreement_id = _agreement(session, company.id, vendor_ids[0], it_leaf)
    return Dataset(company.id, agreement_id, len(catalog))


def grow(session: Session, company_id: str, lines: int, seed: int) -> None:
    """More lines like the company's existing ones, on new invoices of the same suppliers, as a
    sync would bring them."""
    rng = random.Random(seed)
    sample = session.exec(
        select(InvoiceLine, Invoice.vendor_id)
        .join(Invoice, Invoice.id == InvoiceLine.invoice_id)
        .where(InvoiceLine.company_id == company_id)
        .order_by(InvoiceLine.id).limit(5_000)
    ).all()
    written = 0
    while written < lines:
        size = min(CHUNK, lines - written)
        by_vendor: dict[str, list[InvoiceLine]] = {}
        for line, vendor_id in (rng.choice(sample) for _ in range(size)):
            by_vendor.setdefault(vendor_id, []).append(line)
        invoices, rows = [], []
        for vendor_id, picked in by_vendor.items():
            for start in range(0, len(picked), LINES_PER_INVOICE):
                invoice = Invoice(company_id=company_id, vendor_id=vendor_id,
                                  invoice_date=LAST_DAY - timedelta(days=rng.randrange(30)),
                                  currency="DKK", base_currency="DKK", status="posted")
                invoices.append(invoice)
                rows.extend((invoice, sequence, line) for sequence, line
                            in enumerate(picked[start:start + LINES_PER_INVOICE]))
        session.add_all(invoices)
        session.flush()
        session.execute(insert(InvoiceLine), [_copied_row(*row) for row in rows])
        session.commit()
        written += size


def _copied_row(invoice: Invoice, sequence: int, line: InvoiceLine) -> dict:
    fields = ("company_id", "item_name", "quantity", "unit", "unit_price", "amount",
              "base_amount", "base_currency", "spend_category_id", "status", "level_1",
              "level_2", "level_3", "level_4")
    return {"invoice_id": invoice.id, "sequence": sequence,
            **{name: getattr(line, name) for name in fields}}


def _leaves(session: Session, tree_id: str) -> list[SpendCategory]:
    nodes = session.exec(select(SpendCategory).where(SpendCategory.spend_tree_id == tree_id)).all()
    parents = {node.parent_id for node in nodes}
    return sorted((node for node in nodes if node.id not in parents), key=lambda node: node.name)


def _vendors(session: Session, rng: random.Random, faker: Faker) -> list[str]:
    accounts = load_accounts()
    vendors = [Vendor(name=SUPPLIER[0], vat_number=SUPPLIER[1], country_code="DK")]
    for index in range(1, VENDORS):
        vendors.append(Vendor(name=f"{vendor_name(rng.choice(accounts), faker)} {index}",
                              vat_number=f"DK{30000000 + index}", country_code="DK"))
    session.add_all(vendors)
    session.commit()
    return [vendor.id for vendor in vendors]


def _items(rng: random.Random, faker: Faker, count: int, leaves: list[SpendCategory],
           it_leaf: SpendCategory) -> list[Item]:
    catalog: list[Item] = []
    for name in IT_ITEMS:
        for vendor_index in [0, *range(1, WEBSHOPS + 1)]:
            catalog.append(Item(name, it_leaf, vendor_index, _price(rng)))
    accounts = load_accounts()
    per_account = max(1, (count - len(catalog)) // len(accounts))
    for account_index, account in enumerate(accounts):
        leaf = leaves[account_index % len(leaves)]
        for name in line_descriptions(account["account_code"], per_account, faker):
            catalog.append(Item(name, leaf, rng.randrange(WEBSHOPS + 1, VENDORS), _price(rng)))
    return catalog


def _price(rng: random.Random) -> Decimal:
    return Decimal(rng.randrange(50, 20_000))


def _lines(session: Session, company_id: str, catalog: list[Item], vendor_ids: list[str],
           count: int, rng: random.Random) -> None:
    weights = [1 / (rank + 1) ** 0.8 for rank in range(len(catalog))]
    order = list(range(len(catalog)))
    rng.shuffle(order)
    ranked = [catalog[index] for index in order]
    written = 0
    while written < count:
        size = min(CHUNK, count - written)
        chosen = rng.choices(ranked, weights=weights, k=size)
        _write_chunk(session, company_id, chosen, vendor_ids, rng)
        written += size


def _write_chunk(session: Session, company_id: str, chosen: list[Item], vendor_ids: list[str],
                 rng: random.Random) -> None:
    by_vendor: dict[int, list[Item]] = {}
    for item in chosen:
        by_vendor.setdefault(item.vendor_index, []).append(item)
    invoices, lines = [], []
    for vendor_index, items in by_vendor.items():
        for start in range(0, len(items), LINES_PER_INVOICE):
            on = LAST_DAY - timedelta(days=rng.randrange(DAYS))
            invoice = Invoice(company_id=company_id, vendor_id=vendor_ids[vendor_index],
                              invoice_date=on, currency="DKK", base_currency="DKK",
                              status="posted")
            invoices.append(invoice)
            for sequence, item in enumerate(items[start:start + LINES_PER_INVOICE]):
                lines.append((invoice, sequence, item, rng.randrange(1, 4)))
    session.add_all(invoices)
    session.flush()
    session.execute(insert(InvoiceLine), [_line_row(company_id, *line) for line in lines])
    session.commit()


def _line_row(company_id: str, invoice: Invoice, sequence: int, item: Item,
              quantity: int) -> dict:
    amount = item.unit_price * quantity
    path = node_path(item.category)
    levels = {f"level_{depth + 1}": name for depth, name in enumerate(path[:4])}
    return {"company_id": company_id, "invoice_id": invoice.id, "item_name": item.name,
            "quantity": Decimal(quantity), "unit": "piece", "unit_price": item.unit_price,
            "amount": amount, "base_amount": amount, "base_currency": "DKK",
            "spend_category_id": item.category.id, "status": "ai_categorized",
            "sequence": sequence, **levels}


def _agreement(session: Session, company_id: str, supplier_id: str,
               it_leaf: SpendCategory) -> str:
    file_row = File(company_id=company_id, filename="framework.pdf", file_type="agreement_pdf",
                    storage_path="bench/framework.pdf")
    session.add(file_row)
    session.commit()
    agreement = Agreement(company_id=company_id, file_id=file_row.id, title="IT framework",
                          vendor_id=supplier_id, starts_on=LAST_DAY - timedelta(days=DAYS),
                          currency="DKK", status=AgreementStatus.ACTIVE.value,
                          uploaded_by="bench")
    session.add(agreement)
    session.commit()
    terms = [
        (AgreementTermKind.PREFERRED_SUPPLIER, "IT equipment and accessories", {}),
        (AgreementTermKind.AGREED_PRICE, "Lenovo ThinkPad T14 Gen 5",
         {"item": "Lenovo ThinkPad T14 Gen 5", "unit": "piece", "unit_price": Decimal(8000)}),
        (AgreementTermKind.DISCOUNT, "Accessories", {"discount_percent": Decimal(8)}),
        (AgreementTermKind.VOLUME_COMMITMENT, "IT equipment and accessories",
         {"commitment_amount": Decimal(1_000_000), "commitment_period": "year"}),
    ]
    session.add_all(AgreementTerm(agreement_id=agreement.id, kind=kind.value,
                                  status=AgreementTermStatus.CONFIRMED.value, scope=scope,
                                  currency="DKK", scope_category_ids=[it_leaf.id], **fields)
                    for kind, scope, fields in terms)
    session.commit()
    return agreement.id
