"""Putting an estimate onto the voucher and line payloads Spend Lines reads."""
from __future__ import annotations

from decimal import Decimal

from ..schemas.emissions import EmissionCalculationRead, EmissionDeflationRead
from ..schemas.erp.entries import VoucherGroupRead
from ..schemas.invoices.lines import InvoiceLineRead
from .deflation import Deflation
from .results import LineEmissions, VoucherEmissions

MONEY_PLACES = Decimal("0.01")


def with_emissions(group: VoucherGroupRead, result: VoucherEmissions | None) -> VoucherGroupRead:
    """`group` with its kg CO2e and status, and each estimated line's calculation."""
    if result is None:
        return group
    return group.model_copy(update={
        "kg_co2e": result.kg_co2e,
        "emissions_status": result.status.value,
        "lines": lines_with_emissions(group.lines, result),
    })


def lines_with_emissions(lines: list[InvoiceLineRead],
                         result: VoucherEmissions | None) -> list[InvoiceLineRead]:
    """Each line with its kg, factor area and calculation, where it was estimated."""
    if result is None:
        return lines
    updated = []
    for line in lines:
        estimate = result.lines.get(line.id)
        if estimate is None:
            updated.append(line)
        else:
            updated.append(line.model_copy(update={
                "kg_co2e": estimate.kg_co2e,
                "emission_area": estimate.area,
                "emission_calculation": _calculation(line, estimate),
            }))
    return updated


def _calculation(line: InvoiceLineRead, estimate: LineEmissions) -> EmissionCalculationRead:
    converted = estimate.spend * estimate.rate
    return EmissionCalculationRead(
        spend=estimate.spend,
        currency=estimate.currency,
        rate=estimate.rate,
        rate_date=estimate.rate_date,
        converted=converted.quantize(MONEY_PLACES),
        deflation=_deflation(converted, estimate.deflation),
        factor=estimate.factor,
        factor_currency=estimate.factor_currency,
        factor_area=estimate.area,
        sector=line.emission_sector,
        kg_co2e=estimate.kg_co2e,
    )


def _deflation(converted: Decimal, deflation: Deflation | None) -> EmissionDeflationRead | None:
    if deflation is None:
        return None
    return EmissionDeflationRead(
        series=deflation.series,
        label=deflation.label,
        month=deflation.month,
        index=deflation.index,
        base_year=deflation.base_year,
        base_index=deflation.base_index.quantize(Decimal("0.0001")),
        deflated=(converted * deflation.ratio).quantize(MONEY_PLACES),
    )
