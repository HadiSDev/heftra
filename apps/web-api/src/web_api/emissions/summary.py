"""The emissions of every voucher a Spend Lines filter lists, added up."""
from __future__ import annotations

from collections import Counter
from collections.abc import Iterable
from decimal import Decimal
from typing import NamedTuple

from ..schemas.emissions import EmissionsSpendRow, EmissionsSummaryRead, FactorSetRead
from ..vouchers.amounts import ZERO
from .results import VoucherEmissions


class SummarizedVoucher(NamedTuple):
    currency: str
    posted_spend: Decimal | None
    emissions: VoucherEmissions


def summarize(factor_set: FactorSetRead | None,
              vouchers: Iterable[SummarizedVoucher]) -> EmissionsSummaryRead:
    posted: dict[str, Decimal] = {}
    estimated: dict[str, Decimal] = {}
    statuses: Counter[str] = Counter()
    kg = ZERO
    for voucher in vouchers:
        posted[voucher.currency] = posted.get(voucher.currency, ZERO) + (voucher.posted_spend or ZERO)
        estimated[voucher.currency] = (
            estimated.get(voucher.currency, ZERO) + voucher.emissions.estimated_spend
        )
        statuses[voucher.emissions.status.value] += 1
        kg += voucher.emissions.kg_co2e or ZERO
    return EmissionsSummaryRead(
        factor_set=factor_set,
        kg_co2e=kg if factor_set is not None else None,
        spend=[
            EmissionsSpendRow(currency=currency, posted_spend=posted[currency],
                              estimated_spend=estimated[currency])
            for currency in sorted(posted)
        ],
        vouchers_by_status=dict(statuses),
    )
