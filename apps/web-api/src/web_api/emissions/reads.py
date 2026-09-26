"""Putting an estimate onto the voucher payloads Spend Lines reads."""
from __future__ import annotations

from ..schemas.erp.entries import VoucherGroupRead
from .results import VoucherEmissions


def with_emissions(group: VoucherGroupRead, result: VoucherEmissions | None) -> VoucherGroupRead:
    """`group` with its kg CO2e and status, and each estimated line's kg and factor area."""
    if result is None:
        return group
    lines = []
    for line in group.lines:
        estimate = result.lines.get(line.id)
        if estimate is None:
            lines.append(line)
        else:
            lines.append(line.model_copy(
                update={"kg_co2e": estimate.kg_co2e, "emission_area": estimate.area}
            ))
    return group.model_copy(update={
        "kg_co2e": result.kg_co2e,
        "emissions_status": result.status.value,
        "lines": lines,
    })
