"""Items' cheaper alternatives: the list, an item with its specification, and their review."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlmodel import Session

from web_api.db.models import AlternativeMatch, AlternativeSource, ItemClass
from ..alternatives.access import get_alternative, get_item, get_line
from ..alternatives.listing import AlternativeFilters, list_items
from ..alternatives.reads import alternative_reads, item_read
from ..alternatives.review import review_alternative
from ..alternatives.search_requests import request_item_search
from ..alternatives.specification import correct_specification
from ..auth.deps import (
    TenantScope,
    get_session,
    require_management,
    resolve_company_ids,
    tenant_scope,
)
from ..schemas import PipelineRunRead
from ..schemas.alternatives import AlternativeRead, AlternativeReview, AlternativesPage, ItemRead
from ..items.line_item import ensure_line_item, line_item
from ..specs.specification import Specification

router = APIRouter(prefix="/api/v1", tags=["alternatives"])


@router.get("/alternatives", response_model=AlternativesPage)
def list_alternatives(
    company_id: str | None = Query(default=None),
    source: AlternativeSource | None = Query(default=None),
    match: AlternativeMatch | None = Query(default=None),
    item_class: ItemClass | None = Query(default=None),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    scope: TenantScope = Depends(tenant_scope),
    session: Session = Depends(get_session),
) -> AlternativesPage:
    """Items with an open alternative, the largest best yearly saving first."""
    company_ids = resolve_company_ids(scope, company_id)
    if not company_ids:
        return AlternativesPage(items=[], page=page, page_size=page_size, total=0)
    return list_items(session, company_ids, AlternativeFilters(source, match, item_class),
                      page, page_size)


@router.get("/items/{item_id}", response_model=ItemRead)
def read_item(
    item_id: str,
    scope: TenantScope = Depends(tenant_scope),
    session: Session = Depends(get_session),
) -> ItemRead:
    """An item with its specification, price, alternatives and whether it is being searched."""
    return item_read(session, get_item(session, scope, item_id))


@router.patch("/items/{item_id}/specification", response_model=ItemRead)
def update_specification(
    item_id: str,
    body: Specification,
    scope: TenantScope = Depends(require_management),
    session: Session = Depends(get_session),
) -> ItemRead:
    """Correct an item's specification; it is kept from then on and the item searched again."""
    item = get_item(session, scope, item_id)
    correct_specification(session, item, body, scope.user_id)
    session.commit()
    return item_read(session, item)


@router.post("/items/{item_id}/find-alternatives", response_model=PipelineRunRead,
             status_code=status.HTTP_202_ACCEPTED)
def find_alternatives(
    item_id: str,
    scope: TenantScope = Depends(require_management),
    session: Session = Depends(get_session),
):
    """Queue a search of the item's alternatives, or return the one already queued."""
    run = request_item_search(session, get_item(session, scope, item_id), scope.user_id)
    session.commit()
    session.refresh(run)
    return run


@router.get("/invoice-lines/{line_id}/item", response_model=ItemRead)
def read_line_item(
    line_id: str,
    scope: TenantScope = Depends(tenant_scope),
    session: Session = Depends(get_session),
) -> ItemRead:
    """The item a spend line bought, once it is stored."""
    item = line_item(session, get_line(session, scope, line_id))
    if item is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND,
                            detail="This line's item has not been looked at yet.")
    return item_read(session, item)


@router.post("/invoice-lines/{line_id}/find-alternatives", response_model=ItemRead,
             status_code=status.HTTP_202_ACCEPTED)
def find_line_alternatives(
    line_id: str,
    scope: TenantScope = Depends(require_management),
    session: Session = Depends(get_session),
) -> ItemRead:
    """Queue a search of the alternatives of the item a spend line bought."""
    item = ensure_line_item(session, get_line(session, scope, line_id))
    request_item_search(session, item, scope.user_id)
    session.commit()
    return item_read(session, item)


@router.patch("/alternatives/{alternative_id}", response_model=AlternativeRead)
def update_alternative(
    alternative_id: str,
    body: AlternativeReview,
    scope: TenantScope = Depends(require_management),
    session: Session = Depends(get_session),
) -> AlternativeRead:
    """Dismiss an alternative with a reason, mark that the company switched, or reopen it."""
    alternative = get_alternative(session, scope, alternative_id)
    review_alternative(session, alternative, body, scope.user_id)
    session.commit()
    session.refresh(alternative)
    return alternative_reads(session, [alternative])[0]
