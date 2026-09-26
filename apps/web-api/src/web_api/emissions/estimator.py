"""kg CO2e for a voucher: its spend split across its lines, converted, times each line's factor."""
from __future__ import annotations

from collections.abc import Callable
from datetime import date
from decimal import Decimal

from ..vouchers.amounts import ZERO
from ..vouchers.shares import split
from .factors import FactorLookup
from .inputs import LineInput, VoucherInput
from .results import LineEmissions, VoucherEmissions
from .status import EmissionsStatus

KG_PLACES = Decimal("0.001")

RateFor = Callable[[str, date], Decimal | None]


class Estimator:
    """Estimates vouchers with one factor set's factors, converting spend with `rate_for`."""

    def __init__(self, lookup: FactorLookup, rate_for: RateFor) -> None:
        self._lookup = lookup
        self._rate_for = rate_for

    @staticmethod
    def without_factors() -> VoucherEmissions:
        """What every voucher is when no factor set is active."""
        return _nothing(EmissionsStatus.NO_FACTOR_SET)

    def estimate(self, voucher: VoucherInput) -> VoucherEmissions:
        if not voucher.amount:
            return _nothing(EmissionsStatus.NO_SPEND)
        if not voucher.lines:
            return _nothing(EmissionsStatus.NO_LINES)
        if voucher.unconverted or voucher.currency is None:
            return _nothing(EmissionsStatus.UNCONVERTED)

        shares = split(voucher.amount, _weights(voucher.lines))
        sectors = {line.line_id: line.sector_id for line in voucher.lines}
        spent = {line_id: share for line_id, share in shares.items() if share}
        if not any(sectors[line_id] for line_id in spent):
            return _nothing(EmissionsStatus.UNMATCHED)

        rate = self._rate_for(voucher.currency, voucher.spent_on)
        if rate is None:
            return _nothing(EmissionsStatus.UNCONVERTED)

        lines: dict[str, LineEmissions] = {}
        for line_id, share in spent.items():
            sector_id = sectors[line_id]
            factor = self._lookup.find(sector_id, voucher.supplier_country,
                                       voucher.company_country) if sector_id else None
            if factor is not None:
                kg = (share * rate * factor.kg_co2e_per_unit).quantize(KG_PLACES)
                lines[line_id] = LineEmissions(kg, factor.area)

        if not lines:
            return _nothing(EmissionsStatus.NO_FACTOR)
        estimated = sum((spent[line_id] for line_id in lines), ZERO)
        status = EmissionsStatus.ESTIMATED if len(lines) == len(spent) else EmissionsStatus.PARTIAL
        return VoucherEmissions(
            kg_co2e=sum((line.kg_co2e for line in lines.values()), ZERO),
            status=status,
            estimated_spend=estimated,
            lines=lines,
        )


def _weights(lines: list[LineInput]) -> dict[str, Decimal]:
    """Each line's share of the voucher; a discount with no sector is absorbed by the others."""
    return {
        line.line_id: line.base_amount
        for line in lines
        if line.base_amount is not None and (line.sector_id or line.base_amount >= 0)
    }


def _nothing(status: EmissionsStatus) -> VoucherEmissions:
    return VoucherEmissions(kg_co2e=None, status=status, estimated_spend=ZERO, lines={})
