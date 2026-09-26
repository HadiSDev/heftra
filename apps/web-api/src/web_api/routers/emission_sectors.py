"""Searching the active factor set's emission sectors, for the sector picker."""
from __future__ import annotations

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, or_
from sqlmodel import Session, select

from web_api.db.models import EmissionSector
from ..auth.deps import TenantScope, get_session, tenant_scope
from ..emissions.factors import active_factor_set
from ..schemas.emissions import EmissionSectorRead

router = APIRouter(prefix="/api/v1", tags=["emissions"])


@router.get("/emission-sectors", response_model=list[EmissionSectorRead])
def search_emission_sectors(
    q: str = Query(default="", max_length=100),
    limit: int = Query(default=20, ge=1, le=50),
    scope: TenantScope = Depends(tenant_scope),
    session: Session = Depends(get_session),
) -> list[EmissionSectorRead]:
    """Sectors of the active classification whose code or name contains `q`, by name."""
    factor_set = active_factor_set(session)
    if factor_set is None:
        return []
    statement = select(EmissionSector).where(
        EmissionSector.classification == factor_set.classification
    )
    text = q.strip().lower()
    if text:
        pattern = f"%{text}%"
        statement = statement.where(or_(
            func.lower(EmissionSector.name).like(pattern),
            func.lower(EmissionSector.code).like(pattern),
        ))
    sectors = session.exec(statement.order_by(EmissionSector.name).limit(limit)).all()
    return [EmissionSectorRead.model_validate(sector) for sector in sectors]
