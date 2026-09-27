"""Everything the Emission factors admin page shows, in one read."""
from __future__ import annotations

from sqlmodel import Session

from ..schemas.admin import EmissionFactorsStatusRead
from .coverage import coverage_rows
from .factor_sets import factor_set_rows
from .price_indices import price_index_rows


def emission_factors_status(session: Session) -> EmissionFactorsStatusRead:
    return EmissionFactorsStatusRead(
        sets=factor_set_rows(session),
        price_indices=price_index_rows(session),
        coverage=coverage_rows(session),
    )
