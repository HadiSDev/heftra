"""Finding an agreement, term or finding the caller may see or change."""
from __future__ import annotations

from fastapi import HTTPException, status
from sqlmodel import Session

from ..auth.deps import TenantScope
from ..db.models import Agreement, AgreementFinding, AgreementTerm


def _visible(scope: TenantScope, company_id: str) -> bool:
    return scope.is_system_admin or company_id in scope.company_ids


def _not_found(what: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"{what} not found")


def get_agreement(session: Session, scope: TenantScope, agreement_id: str) -> Agreement:
    agreement = session.get(Agreement, agreement_id)
    if agreement is None or not _visible(scope, agreement.company_id):
        raise _not_found("Agreement")
    return agreement


def get_term(session: Session, scope: TenantScope, term_id: str) -> tuple[AgreementTerm, Agreement]:
    term = session.get(AgreementTerm, term_id)
    if term is None:
        raise _not_found("Term")
    return term, get_agreement(session, scope, term.agreement_id)


def get_finding(session: Session, scope: TenantScope, finding_id: str) -> AgreementFinding:
    finding = session.get(AgreementFinding, finding_id)
    if finding is None or not _visible(scope, finding.company_id):
        raise _not_found("Finding")
    return finding
