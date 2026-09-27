"""How many of each company's invoice lines have an emission sector in the active classification."""
from __future__ import annotations

from decimal import Decimal

from sqlalchemy import and_, case, func
from sqlmodel import Session, select

from .. import config
from ..db.models import (
    Company,
    EmissionSector,
    EmissionSectorSource,
    InvoiceLine,
    Organization,
)
from ..emissions.factors import active_factor_set
from ..schemas.admin import SectorCoverageRow


def coverage_rows(session: Session) -> list[SectorCoverageRow]:
    factor_set = active_factor_set(session)
    classification = factor_set.classification if factor_set is not None else None
    in_active = EmissionSector.classification == classification
    is_ai = and_(in_active, InvoiceLine.emission_sector_source == EmissionSectorSource.AI)
    is_human = and_(in_active, InvoiceLine.emission_sector_source == EmissionSectorSource.HUMAN)
    unsure = and_(is_ai, InvoiceLine.emission_sector_confidence
                  < Decimal(str(config.CATEGORIZATION_REVIEW_THRESHOLD)))

    rows = session.exec(
        select(
            Company.id, Company.name, Organization.name,
            func.count(InvoiceLine.id),
            func.sum(case((is_ai, 1), else_=0)),
            func.sum(case((is_human, 1), else_=0)),
            func.sum(case((unsure, 1), else_=0)),
        )
        .join(Organization, Organization.id == Company.organization_id)
        .outerjoin(InvoiceLine, InvoiceLine.company_id == Company.id)
        .outerjoin(EmissionSector, EmissionSector.id == InvoiceLine.emission_sector_id)
        .group_by(Company.id, Company.name, Organization.name)
        .order_by(Organization.name, Company.name)
    ).all()
    return [
        SectorCoverageRow(
            company_id=company_id, company_name=company_name, organization_name=org_name,
            lines=lines, ai=ai or 0, human=human or 0, needs_review=unsure_count or 0,
            unmatched=lines - (ai or 0) - (human or 0),
        )
        for company_id, company_name, org_name, lines, ai, human, unsure_count in rows
    ]
