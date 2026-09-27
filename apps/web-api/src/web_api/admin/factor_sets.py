"""Every factor set with its sector and factor counts, active first."""
from __future__ import annotations

from sqlalchemy import func
from sqlmodel import Session, col, select

from ..db.models import EmissionFactor, EmissionFactorSet, EmissionSector
from ..schemas.admin import AdminFactorSetRead


def factor_set_rows(session: Session) -> list[AdminFactorSetRead]:
    sets = session.exec(
        select(EmissionFactorSet).order_by(col(EmissionFactorSet.active).desc(),
                                           col(EmissionFactorSet.imported_at).desc())
    ).all()
    factors = dict(session.exec(
        select(EmissionFactor.factor_set_id, func.count())
        .group_by(EmissionFactor.factor_set_id)
    ).all())
    sectors = dict(session.exec(
        select(EmissionSector.classification, func.count())
        .group_by(EmissionSector.classification)
    ).all())
    return [admin_factor_set(factor_set, sectors=sectors.get(factor_set.classification, 0),
                             factors=factors.get(factor_set.id, 0))
            for factor_set in sets]


def admin_factor_set(factor_set: EmissionFactorSet, *, sectors: int,
                     factors: int) -> AdminFactorSetRead:
    return AdminFactorSetRead(
        id=factor_set.id, source=factor_set.source, version=factor_set.version,
        classification=factor_set.classification, currency=factor_set.currency,
        price_year=factor_set.price_year, price_basis=factor_set.price_basis,
        attribution=factor_set.attribution, sectors=sectors, factors=factors,
        imported_at=factor_set.imported_at, active=factor_set.active,
    )


def counted_factor_set(session: Session, factor_set: EmissionFactorSet) -> AdminFactorSetRead:
    """One set with its counts."""
    factors = session.exec(
        select(func.count()).select_from(EmissionFactor)
        .where(EmissionFactor.factor_set_id == factor_set.id)
    ).one()
    sectors = session.exec(
        select(func.count()).select_from(EmissionSector)
        .where(EmissionSector.classification == factor_set.classification)
    ).one()
    return admin_factor_set(factor_set, sectors=sectors, factors=factors)
