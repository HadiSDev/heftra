"""Invoices by the state of their document: read and failed, or read and disagreeing with the ERP."""
from __future__ import annotations

from typing import Literal

from sqlalchemy import or_
from sqlmodel import Session, select

from web_api.db.models import ErpEntry, Invoice
from web_api.db.models.enums import DocStatus
from web_api.reconcile import totals_agree

DocumentFilter = Literal["failed", "mismatch"]


def failed_invoice_ids(company_ids: list[str]):
    """The companies' invoices whose document could not be read, as a subquery."""
    return select(Invoice.id).where(
        Invoice.company_id.in_(company_ids), Invoice.doc_status == DocStatus.FAILED.value,
    )


def mismatched_invoice_ids(session: Session, company_ids: list[str]) -> set[str]:
    """The companies' invoices whose document total disagrees with the ERP's beyond the tolerance."""
    documented = session.exec(
        select(Invoice).where(
            Invoice.company_id.in_(company_ids),
            or_(Invoice.document_total.is_not(None), Invoice.document_subtotal.is_not(None)),
        )
    ).all()
    return {invoice.id for invoice in documented if totals_agree(invoice) is False}


def document_condition(session: Session, company_ids: list[str], document: DocumentFilter):
    """The postings whose invoice's document is in the given state."""
    if document == "failed":
        return ErpEntry.source_invoice_id.in_(failed_invoice_ids(company_ids))
    return ErpEntry.source_invoice_id.in_(mismatched_invoice_ids(session, company_ids))
