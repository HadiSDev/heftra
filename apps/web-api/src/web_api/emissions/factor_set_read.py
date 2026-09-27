"""The active factor set as the Spend Lines summary and the dashboard report show it."""
from __future__ import annotations

from sqlmodel import Session

from ..db.models import EmissionFactorSet
from ..schemas.emissions import FactorSetRead, PriceIndexRead
from .deflation import Deflator


def factor_set_read(session: Session, factor_set: EmissionFactorSet) -> FactorSetRead:
    """The set, with the price index its estimates are deflated with, if any."""
    deflator = Deflator.for_factor_set(session, factor_set)
    price_index = None
    if deflator is not None:
        price_index = PriceIndexRead(series=deflator.series.id, label=deflator.series.label,
                                     latest_month=deflator.index.latest_month)
    return FactorSetRead.model_validate(factor_set).model_copy(update={"price_index": price_index})
