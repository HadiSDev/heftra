"""The dashboard's emissions: a period against its comparison, twelve months, the top sectors."""
from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import NamedTuple

from sqlmodel import Session, select

from web_api.db.models import EmissionSector
from web_api.emissions.factors import active_factor_set
from web_api.emissions.results import VoucherEmissions
from web_api.emissions.vouchers import estimate_vouchers
from web_api.fx.service import FxService
from web_api.schemas import MonthEmissions, SectorEmissions, SpendEmissions
from web_api.schemas.emissions import EmissionsSpendRow, FactorSetRead
from web_api.vouchers.amounts import ZERO, voucher_amount
from web_api.vouchers.dates import spent_on
from web_api.vouchers.groups import vouchers_between

from .figures import report_periods
from .periods import Period, month_start, trailing_months

TOP_SECTORS = 5


class _DatedEstimate(NamedTuple):
    spent_on: date
    currency: str | None
    posted: Decimal | None
    emissions: VoucherEmissions


def spend_emissions(session: Session, company_ids: list[str], period: Period) -> SpendEmissions:
    periods = report_periods(period)
    factor_set = active_factor_set(session)
    if factor_set is None:
        return SpendEmissions(**periods.model_dump())

    comparison = period.comparison()
    months = trailing_months(period.end)
    window = Period(min(comparison.start, months[0]), period.end)
    groups = vouchers_between(session, company_ids, window.start, window.end)
    estimates = estimate_vouchers(session, groups, FxService(session))
    dated = []
    for key, rows in groups.items():
        amount, _, _, currency, _ = voucher_amount(rows, "base")
        dated.append(_DatedEstimate(spent_on(rows), currency, amount, estimates[key]))
    in_period = [estimate for estimate in dated if period.contains(estimate.spent_on)]

    return SpendEmissions(
        **periods.model_dump(),
        factor_set=FactorSetRead.model_validate(factor_set),
        kg_co2e=_kg(in_period),
        comparison_kg_co2e=_kg(e for e in dated if comparison.contains(e.spent_on)),
        months=[
            MonthEmissions(month=month, kg_co2e=_kg(
                e for e in dated if month_start(e.spent_on) == month
            ))
            for month in months
        ],
        spend=_spend(in_period),
        top_sectors=_top_sectors(session, in_period),
    )


def _kg(estimates) -> Decimal:
    return sum((estimate.emissions.kg_co2e or ZERO for estimate in estimates), ZERO)


def _spend(estimates: list[_DatedEstimate]) -> list[EmissionsSpendRow]:
    posted: dict[str, Decimal] = {}
    estimated: dict[str, Decimal] = {}
    for estimate in estimates:
        if estimate.currency is None:
            continue
        posted[estimate.currency] = posted.get(estimate.currency, ZERO) + (estimate.posted or ZERO)
        estimated[estimate.currency] = (
            estimated.get(estimate.currency, ZERO) + estimate.emissions.estimated_spend
        )
    return [
        EmissionsSpendRow(currency=currency, posted_spend=posted[currency],
                          estimated_spend=estimated[currency])
        for currency in sorted(posted)
    ]


def _top_sectors(session: Session, estimates: list[_DatedEstimate]) -> list[SectorEmissions]:
    by_sector: dict[str, Decimal] = {}
    for estimate in estimates:
        for line in estimate.emissions.lines.values():
            by_sector[line.sector_id] = by_sector.get(line.sector_id, ZERO) + line.kg_co2e
    top = sorted(by_sector.items(), key=lambda item: item[1], reverse=True)[:TOP_SECTORS]
    if not top:
        return []
    sectors = {
        sector.id: sector
        for sector in session.exec(
            select(EmissionSector).where(
                EmissionSector.id.in_([sector_id for sector_id, _ in top])  # type: ignore[attr-defined]
            )
        ).all()
    }
    return [
        SectorEmissions(code=sectors[sector_id].code, name=sectors[sector_id].name, kg_co2e=kg)
        for sector_id, kg in top
    ]
