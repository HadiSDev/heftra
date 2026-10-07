"""Give every demo invoice the scanned document a real ERP sync would have attached.

The documents themselves are served by the demo ERP (apps/demo/erp), so this only writes the
`files` rows and marks each invoice's document as processed, with the totals it states.
Run from the repository root with DATABASE_URL pointing at the demo build database.
"""
from __future__ import annotations

import uuid
from datetime import datetime, time, timezone

from sqlmodel import Session, select

from web_api.db.models import DocStatus, ErpEntry, File, Invoice, Vendor
from web_api.db.session import engine

COMPANY_ID = "1488f6e8-023f-5c1c-99b4-1a6a286f18c0"
FILE_TYPE = "invoice_pdf"
NAMESPACE = uuid.UUID("6c0f3f86-3a9a-4b9c-9a51-7c1d2f5e8a10")


def _voucher(session: Session, invoice: Invoice) -> str | None:
    return session.exec(
        select(ErpEntry.voucher_id)
        .where(ErpEntry.source_invoice_id == invoice.id, ErpEntry.voucher_id.is_not(None))
        .order_by(ErpEntry.id)
    ).first()


def _attach(session: Session, invoice: Invoice) -> bool:
    voucher_id = _voucher(session, invoice)
    if voucher_id is None:
        return False
    file_id = str(uuid.uuid5(NAMESPACE, invoice.id))
    if session.get(File, file_id) is None:
        session.add(File(
            id=file_id, company_id=COMPANY_ID, filename=f"{invoice.invoice_number}.pdf",
            file_type=FILE_TYPE, storage_path=f"erp-voucher:{voucher_id}", status="processed",
        ))
    vendor = session.get(Vendor, invoice.vendor_id) if invoice.vendor_id else None
    invoice.file_id = file_id
    invoice.doc_status = DocStatus.PROCESSED
    invoice.doc_processed_at = datetime.combine(invoice.invoice_date, time(9), timezone.utc)
    invoice.document_invoice_number = invoice.invoice_number
    invoice.document_total = invoice.total
    invoice.document_tax = invoice.tax
    invoice.document_subtotal = invoice.total - invoice.tax
    invoice.document_supplier_country_code = invoice.supplier_country_code
    invoice.document_supplier_vat_number = invoice.supplier_vat_number
    invoice.document_supplier_website = vendor.website if vendor else None
    session.add(invoice)
    return True


def main() -> None:
    with Session(engine) as session:
        invoices = session.exec(select(Invoice).where(Invoice.company_id == COMPANY_ID)).all()
        attached = sum(1 for invoice in invoices if _attach(session, invoice))
        session.commit()
    print(f"Attached documents to {attached} of {len(invoices)} invoices.")


if __name__ == "__main__":
    main()
