"""Where a company buys: its country, language and currency, for searching shops there."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Market:
    country: str
    language: str
    currency: str

    @property
    def key(self) -> str:
        return f"{self.country}-{self.language}".lower()

    @property
    def locale(self) -> str:
        return f"{self.language}-{self.country}"


MARKETS: dict[str, Market] = {
    "DK": Market("DK", "da", "DKK"),
    "SE": Market("SE", "sv", "SEK"),
    "NO": Market("NO", "nb", "NOK"),
    "FI": Market("FI", "fi", "EUR"),
    "DE": Market("DE", "de", "EUR"),
    "NL": Market("NL", "nl", "EUR"),
    "GB": Market("GB", "en", "GBP"),
}


def market_for(country_code: str | None) -> Market | None:
    """The market of a company's country; None when it has none or it isn't served yet."""
    return MARKETS.get((country_code or "").upper())
