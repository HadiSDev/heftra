"""A company's books for the spend reports' tests: accounts, suppliers, invoices, lines and postings."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlmodel import Session

from web_api.db.models import (
    Company,
    ErpAccount,
    ErpEntry,
    ErpIntegration,
    Invoice,
    InvoiceLine,
    Organization,
    Vendor,
)


class Books:
    """One company's ledger, written straight into the session."""

    def __init__(self, session: Session, *, name: str = "Acme A/S", currency: str = "DKK",
                 organization_id: str | None = None) -> None:
        self.session = session
        if organization_id is None:
            organization = Organization(name=f"{name} org", clerk_org_id=f"clerk_{name}")
            session.add(organization)
            session.commit()
            organization_id = organization.id
        self.organization_id = organization_id
        self.company = Company(organization_id=organization_id, name=name, base_currency=currency)
        session.add(self.company)
        session.commit()
        integration = ErpIntegration(company_id=self.company.id, erp_type="mock", label="ERP")
        session.add(integration)
        session.commit()
        self.expense = self._account(integration.id, "1830", "expense", synced=True)
        self.vat = self._account(integration.id, "7220", "liability", synced=False)
        self.payable = self._account(integration.id, "7320", "liability", synced=False)
        self._vouchers = 0

    def _account(self, integration_id: str, code: str, kind: str, *, synced: bool) -> ErpAccount:
        account = ErpAccount(erp_integration_id=integration_id, erp_account_code=code,
                             erp_account_name=code, erp_account_type=kind, sync_enabled=synced)
        self.session.add(account)
        self.session.commit()
        return account

    def supplier(self, name: str) -> Vendor:
        vendor = Vendor(name=name)
        self.session.add(vendor)
        self.session.commit()
        return vendor

    def purchase(
        self,
        on: date,
        net: str,
        *,
        vendor: Vendor | None = None,
        lines: list[tuple[str, str | None, str | None, str]] | None = None,
        vat: str = "0",
        converted: bool = True,
        invoice_date: date | None = None,
    ) -> Invoice | None:
        """Post a purchase of `net` on `on`; lines are (amount, level_1, level_2, status)."""
        self._vouchers += 1
        voucher = f"{self.company.id}-{self._vouchers}"
        invoice = None
        if vendor is not None or lines is not None:
            invoice = Invoice(company_id=self.company.id, vendor_id=vendor.id if vendor else None,
                              invoice_date=invoice_date or on, currency=self.company.base_currency,
                              status="uncategorized")
            self.session.add(invoice)
            self.session.commit()
            for sequence, (amount, level_1, level_2, status) in enumerate(lines or []):
                self.session.add(InvoiceLine(
                    company_id=self.company.id, invoice_id=invoice.id, sequence=sequence,
                    amount=Decimal(amount), base_amount=Decimal(amount),
                    base_currency=self.company.base_currency, level_1=level_1, level_2=level_2,
                    status=status, confidence=Decimal("0.9"),
                ))
        self._post(voucher, self.expense, on, debit=net, invoice=invoice, converted=converted)
        if Decimal(vat):
            self._post(voucher, self.vat, on, debit=vat, invoice=invoice, converted=converted)
        self.session.commit()
        return invoice

    def _post(self, voucher: str, account: ErpAccount, on: date, *, debit: str,
              invoice: Invoice | None, converted: bool) -> None:
        amount = Decimal(debit)
        self.session.add(ErpEntry(
            company_id=self.company.id, erp_account_id=account.id, voucher_id=voucher,
            source_invoice_id=invoice.id if invoice else None, entry_type="purchase_invoice",
            accounting_date=on, debit_amount=amount, currency=self.company.base_currency,
            base_currency=self.company.base_currency if converted else None,
            base_debit_amount=amount if converted else None,
        ))
