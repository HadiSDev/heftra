"""Reviewing what analysis found against an agreement."""
from __future__ import annotations

from fastapi import APIRouter, Depends
from sqlmodel import Session

from ..agreements.access import get_finding
from ..agreements.review import review_finding
from ..auth.deps import TenantScope, get_session, require_management
from ..compliance.findings import finding_read
from ..schemas.agreements import FindingRead, FindingReview

router = APIRouter(prefix="/api/v1", tags=["agreements"])


@router.patch("/agreement-findings/{finding_id}", response_model=FindingRead)
def update_finding(
    finding_id: str,
    body: FindingReview,
    scope: TenantScope = Depends(require_management),
    session: Session = Depends(get_session),
) -> FindingRead:
    """Accept a finding as an exception, rule it out of scope, or reopen it."""
    finding = get_finding(session, scope, finding_id)
    review_finding(session, finding, body, scope.user_id)
    session.commit()
    return finding_read(session, finding.id)
