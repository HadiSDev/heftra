"""Finding an item or an alternative the caller may see or change."""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlmodel import Session

from ..auth.deps import TenantScope
from ..db.models import CompanyItem, InvoiceLine, ItemAlternative

AUDIT_ITEM = "company_item"
AUDIT_ALTERNATIVE = "item_alternative"


def get_item(session: Session, scope: TenantScope, item_id: str) -> CompanyItem:
    item = session.get(CompanyItem, item_id)
    if item is None or not _visible(scope, item.company_id):
        raise _not_found("Item")
    return item


def get_alternative(session: Session, scope: TenantScope, alternative_id: str) -> ItemAlternative:
    alternative = session.get(ItemAlternative, alternative_id)
    if alternative is None or not _visible(scope, alternative.company_id):
        raise _not_found("Alternative")
    return alternative


def get_line(session: Session, scope: TenantScope, line_id: str) -> InvoiceLine:
    line = session.get(InvoiceLine, line_id)
    if line is None or not _visible(scope, line.company_id):
        raise _not_found("Invoice line")
    return line


def _visible(scope: TenantScope, company_id: str) -> bool:
    return scope.is_system_admin or company_id in scope.company_ids


def _not_found(what: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{what} not found")
