"""Adding and reviewing an agreement's terms."""
from __future__ import annotations

from fastapi import APIRouter, Depends, status
from sqlmodel import Session

from ..agreements.access import get_agreement, get_term
from ..agreements.terms import add_term, patch_term
from ..auth.deps import TenantScope, get_session, require_management
from ..schemas.agreements import TermCreate, TermPatch, TermRead

router = APIRouter(prefix="/api/v1", tags=["agreements"])


@router.post("/agreements/{agreement_id}/terms", response_model=TermRead,
             status_code=status.HTTP_201_CREATED)
def create_term(
    agreement_id: str,
    body: TermCreate,
    scope: TenantScope = Depends(require_management),
    session: Session = Depends(get_session),
) -> TermRead:
    """A term the reader missed, confirmed as written."""
    agreement = get_agreement(session, scope, agreement_id)
    term = add_term(session, agreement, body, scope.user_id)
    session.commit()
    session.refresh(term)
    return TermRead.model_validate(term)


@router.patch("/agreement-terms/{term_id}", response_model=TermRead)
def update_term(
    term_id: str,
    body: TermPatch,
    scope: TenantScope = Depends(require_management),
    session: Session = Depends(get_session),
) -> TermRead:
    """Edit, confirm or reject a term."""
    term, agreement = get_term(session, scope, term_id)
    patch_term(session, agreement, term, body, scope.user_id)
    session.commit()
    session.refresh(term)
    return TermRead.model_validate(term)
