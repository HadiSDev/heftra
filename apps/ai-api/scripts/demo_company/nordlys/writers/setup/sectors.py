"""The emission sectors of the active factor set that the catalog names by code."""
from __future__ import annotations

from sqlmodel import Session, col, select

from web_api.db.models import EmissionFactorSet, EmissionSector


class MissingSectors(LookupError):
    """The active factor set's classification lacks sectors the catalog uses."""


def active_sectors(session: Session, codes: set[str]) -> dict[str, EmissionSector]:
    """The sectors by code; raises when there is no active factor set or a code is missing."""
    factor_set = session.exec(
        select(EmissionFactorSet).where(EmissionFactorSet.active == True)  # noqa: E712
    ).first()
    if factor_set is None:
        raise MissingSectors("No emission factor set is active.")
    sectors = session.exec(
        select(EmissionSector).where(EmissionSector.classification == factor_set.classification,
                                     col(EmissionSector.code).in_(codes))
    ).all()
    found = {sector.code: sector for sector in sectors}
    missing = codes - set(found)
    if missing:
        raise MissingSectors(f"Sectors missing from {factor_set.classification}: "
                             f"{', '.join(sorted(missing))}")
    return found
