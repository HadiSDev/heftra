"""Standard VAT rates by country, to take VAT out of a price stated with it."""
from __future__ import annotations

from decimal import Decimal

STANDARD_VAT_PERCENT: dict[str, Decimal] = {
    "AT": Decimal("20"), "BE": Decimal("21"), "BG": Decimal("20"), "CH": Decimal("8.1"),
    "CY": Decimal("19"), "CZ": Decimal("21"), "DE": Decimal("19"), "DK": Decimal("25"),
    "EE": Decimal("24"), "ES": Decimal("21"), "FI": Decimal("25.5"), "FR": Decimal("20"),
    "GB": Decimal("20"), "GR": Decimal("24"), "HR": Decimal("25"), "HU": Decimal("27"),
    "IE": Decimal("23"), "IS": Decimal("24"), "IT": Decimal("22"), "LT": Decimal("21"),
    "LU": Decimal("17"), "LV": Decimal("21"), "MT": Decimal("18"), "NL": Decimal("21"),
    "NO": Decimal("25"), "PL": Decimal("23"), "PT": Decimal("23"), "RO": Decimal("19"),
    "SE": Decimal("25"), "SI": Decimal("22"), "SK": Decimal("23"),
}


def without_vat(price: Decimal, vat_included: bool, country: str | None) -> Decimal | None:
    """The price without VAT; None when it includes VAT at a rate that isn't known."""
    if not vat_included:
        return price
    rate = STANDARD_VAT_PERCENT.get((country or "").upper())
    if rate is None:
        return None
    return price / (1 + rate / 100)
