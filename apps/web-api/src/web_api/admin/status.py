"""Everything the Emission factors page shows, in one read."""
from __future__ import annotations

from sqlmodel import Session

from ..schemas.admin import EmissionFactorsStatusRead
from .coverage import coverage_rows
from .factor_sets import factor_set_rows
from .price_indices import price_index_rows


def emission_factors_status(
    session: Session, company_ids: list[str] | None = None,
) -> EmissionFactorsStatusRead:
    """Factor sets and price indices in full; coverage for `company_ids`, or every company when None."""
    return EmissionFactorsStatusRead(
        sets=factor_set_rows(session),
        price_indices=price_index_rows(session),
        coverage=coverage_rows(session, company_ids),
    )
