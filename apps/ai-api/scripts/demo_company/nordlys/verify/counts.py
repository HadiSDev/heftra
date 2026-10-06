"""How many rows a company holds in each table the demo writes to."""
from __future__ import annotations

from sqlalchemy import func
from sqlmodel import Session, col, select

from web_api.db.models import (
    Agreement,
    AgreementFinding,
    AgreementTerm,
    AgreementTermSpend,
    CompanyItem,
    ErpAccount,
    ErpEntry,
    ErpIntegration,
    File,
    Invoice,
    InvoiceLine,
    ItemAlternative,
    PipelineRun,
)

COMPANY_SCOPED = {
    "invoices": Invoice,
    "invoice_lines": InvoiceLine,
    "erp_entries": ErpEntry,
    "erp_integrations": ErpIntegration,
    "files": File,
    "company_items": CompanyItem,
    "item_alternatives": ItemAlternative,
    "agreements": Agreement,
    "agreement_findings": AgreementFinding,
    "pipeline_runs": PipelineRun,
}


def table_counts(session: Session, company_id: str) -> dict[str, int]:
    counts = {name: session.exec(select(func.count()).select_from(model)
                                 .where(model.company_id == company_id)).one()
              for name, model in COMPANY_SCOPED.items()}
    agreements = select(Agreement.id).where(Agreement.company_id == company_id)
    terms = select(AgreementTerm.id).where(col(AgreementTerm.agreement_id).in_(agreements))
    integrations = select(ErpIntegration.id).where(ErpIntegration.company_id == company_id)
    counts["agreement_terms"] = session.exec(
        select(func.count()).select_from(AgreementTerm)
        .where(col(AgreementTerm.agreement_id).in_(agreements))).one()
    counts["agreement_term_spend"] = session.exec(
        select(func.count()).select_from(AgreementTermSpend)
        .where(col(AgreementTermSpend.term_id).in_(terms))).one()
    counts["erp_accounts"] = session.exec(
        select(func.count()).select_from(ErpAccount)
        .where(col(ErpAccount.erp_integration_id).in_(integrations))).one()
    return counts
