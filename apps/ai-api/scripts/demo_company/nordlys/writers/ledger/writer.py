"""The planned purchases as the ERP sync and the categorizer leave them: invoices, categorized
lines with emission sectors, and the vouchers' postings."""
from __future__ import annotations

from datetime import date
from decimal import ROUND_HALF_UP, Decimal

from sqlmodel import Session

from web_api.db.models import (
    DocStatus,
    EmissionSectorSource,
    ErpAccount,
    ErpEntry,
    Invoice,
    InvoiceLine,
    LineOrigin,
)

from ...catalog.tree import PAYABLES_ACCOUNT, VAT_ACCOUNT
from ...generation.lines import VERIFIED
from ...generation.planned import PlannedInvoice, PlannedLine
from ...ids import COMPANY_ID, demo_id
from ...settings import CURRENCY, MONEY, VAT_RATE
from .books import Books, invoice_id, line_id
from .rationales import category_rationale, sector_rationale

ONE = Decimal(1)
VAT_PERCENT = VAT_RATE * 100
FIRST_VOUCHER = 4100
PURCHASE = "purchase_invoice"
COUNTRY = "DK"


class LedgerWriter:
    def __init__(self, session: Session, books: Books) -> None:
        self._session = session
        self._books = books

    def write(self, plan: list[PlannedInvoice]) -> None:
        """Add every invoice with its lines and postings; the caller commits."""
        for invoice in plan:
            self._invoice(invoice)
        self._session.flush()
        for voucher_number, invoice in enumerate(plan, start=FIRST_VOUCHER):
            self._postings(invoice, str(voucher_number))
        self._session.flush()

    def _invoice(self, planned: PlannedInvoice) -> None:
        supplier = planned.supplier
        all_verified = all(line.status == VERIFIED for line in planned.lines)
        invoice = Invoice(
            id=invoice_id(planned), company_id=COMPANY_ID,
            vendor_id=self._books.vendors[supplier.key].id, invoice_number=planned.number,
            invoice_date=planned.on, currency=CURRENCY, total=planned.total, tax=planned.tax,
            base_currency=CURRENCY, base_total=planned.total, base_tax=planned.tax, fx_rate=ONE,
            fx_rate_date=planned.on, supplier_name=supplier.name, supplier_country_code=COUNTRY,
            supplier_vat_number=supplier.vat_number,
            status="verified" if all_verified else "categorized", source="erp",
            doc_status=DocStatus.NOT_APPLICABLE)
        self._session.add(invoice)
        for line in planned.lines:
            self._session.add(self._line(planned, line))

    def _line(self, planned: PlannedInvoice, line: PlannedLine) -> InvoiceLine:
        product = line.product
        leaf = self._books.leaves[product.leaf]
        sector = self._books.sectors[product.sector]
        return InvoiceLine(
            id=line_id(planned, line), company_id=COMPANY_ID, invoice_id=invoice_id(planned),
            item_name=product.name, description=product.description, quantity=line.quantity,
            unit=product.unit, unit_price=line.unit_price, amount=line.amount,
            discount=line.discount, tax_rate=VAT_PERCENT,
            tax_amount=(line.amount * VAT_RATE).quantize(MONEY, ROUND_HALF_UP),
            native_account_code=planned.supplier.account, origin=LineOrigin.ERP,
            sequence=line.sequence, base_currency=CURRENCY, base_amount=line.amount,
            fx_rate=ONE, fx_rate_date=planned.on, status=line.status,
            level_1=leaf.level_1, level_2=leaf.level_2, level_3=leaf.level_3,
            account_code=leaf.code, account_name=leaf.name, confidence=line.confidence,
            rationale=category_rationale(product, planned.supplier, leaf, line.confidence),
            spend_category_id=leaf.id, emission_sector_id=sector.id,
            emission_sector_source=EmissionSectorSource.AI,
            emission_sector_confidence=line.sector_confidence,
            emission_sector_rationale=sector_rationale(product, sector))

    def _postings(self, planned: PlannedInvoice, voucher: str) -> None:
        expense = self._books.accounts[planned.supplier.account]
        for line in planned.lines:
            self._post(planned, voucher, f"{voucher}-{line.sequence + 1}", expense,
                       line.product.name, debit=line.amount, line=line)
        self._post(planned, voucher, f"{voucher}-vat", self._books.accounts[VAT_ACCOUNT],
                   "Input VAT", debit=planned.tax)
        self._post(planned, voucher, f"{voucher}-ap", self._books.accounts[PAYABLES_ACCOUNT],
                   planned.supplier.name, credit=planned.total)

    def _post(self, planned: PlannedInvoice, voucher: str, entry: str, account: ErpAccount,
              description: str, *, debit: Decimal | None = None, credit: Decimal | None = None,
              line: PlannedLine | None = None) -> None:
        on: date = planned.on
        self._session.add(ErpEntry(
            id=demo_id("erp-entry", f"{planned.key}:{entry}"), company_id=COMPANY_ID,
            erp_account_id=account.id, source_invoice_id=invoice_id(planned),
            source_invoice_line_id=line_id(planned, line) if line is not None else None,
            voucher_id=voucher, voucher_number=voucher, entry_type=PURCHASE,
            accounting_date=on, description=description, debit_amount=debit,
            credit_amount=credit, currency=CURRENCY, erp_entry_id=entry,
            base_currency=CURRENCY, base_debit_amount=debit, base_credit_amount=credit,
            fx_rate=ONE, fx_rate_date=on))
