"""The price index each imported factor set's currency is deflated with."""
from __future__ import annotations

from sqlmodel import Session, select

from ..db.models import EmissionFactorSet
from ..price_indices.index import PriceIndex
from ..price_indices.series import index_for_currency
from ..schemas.admin import AdminPriceIndexRead


def price_index_rows(session: Session) -> list[AdminPriceIndexRead]:
    sets = session.exec(select(EmissionFactorSet)).all()
    active = next((factor_set for factor_set in sets if factor_set.active), None)
    rows: dict[str, AdminPriceIndexRead] = {}
    for currency in sorted({factor_set.currency for factor_set in sets}):
        series = index_for_currency(currency)
        if series is None or series.id in rows:
            continue
        index = PriceIndex.load(session, series.id)
        base_year = active.price_year if active and active.currency == currency else None
        rows[series.id] = AdminPriceIndexRead(
            series=series.id, label=series.label, currency=currency, months=index.months,
            latest_month=index.latest_month, base_year=base_year,
            base_average=index.average(base_year) if base_year is not None else None,
        )
    return list(rows.values())
