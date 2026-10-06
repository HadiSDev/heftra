"""The demo company and its ERP connection with the chart of accounts."""
from __future__ import annotations

from datetime import datetime, timezone

from sqlmodel import Session

from web_api.db.models import Company, ErpAccount, ErpIntegration

from ...catalog import company as profile
from ...catalog.tree import ACCOUNTS
from ...ids import COMPANY_ID, INTEGRATION_ID, TREE_ID, demo_id
from ...settings import CURRENCY, ORGANIZATION_ID

CREATED_AT = datetime(2025, 1, 8, 9, 30, tzinfo=timezone.utc)
ERP_TYPE = "mock"
ERP_LABEL = "Mock ERP (demo)"


def write_company(session: Session, now: datetime) -> Company:
    """The company, marked as researched so the worker doesn't describe it again."""
    company = Company(
        id=COMPANY_ID, organization_id=ORGANIZATION_ID, name=profile.NAME,
        country_code=profile.COUNTRY, vat_number=profile.VAT_NUMBER, base_currency=CURRENCY,
        spend_tree_id=TREE_ID, website=profile.WEBSITE, description=profile.DESCRIPTION,
        description_source=profile.DESCRIPTION_SOURCE, researched_at=now, is_active=True,
        created_at=CREATED_AT)
    session.add(company)
    session.flush()
    return company


def write_erp(session: Session) -> dict[str, ErpAccount]:
    """The connected ERP and its accounts; returns the accounts by code."""
    session.add(ErpIntegration(id=INTEGRATION_ID, company_id=COMPANY_ID, erp_type=ERP_TYPE,
                               label=ERP_LABEL, connected_at=CREATED_AT, created_at=CREATED_AT))
    session.flush()
    accounts = {}
    for spec in ACCOUNTS:
        account = ErpAccount(
            id=demo_id("erp-account", spec.code), erp_integration_id=INTEGRATION_ID,
            erp_account_code=spec.code, erp_account_name=spec.name, erp_account_type=spec.kind,
            sync_enabled=spec.synced, with_vat=False, is_active=True)
        session.add(account)
        accounts[spec.code] = account
    session.flush()
    return accounts
