"""What every marketplace connector does."""
from __future__ import annotations

from typing import Protocol

from .market import Market
from .offer import Offer


class ConnectorFailed(RuntimeError):
    """A connector could not answer: its provider failed or refused."""


class OfferSource(Protocol):
    """Asked a query (a part number, an EAN, or a product name with its key attributes) in a
    market, returns the offers it finds; raises `ConnectorFailed` when it can't answer."""

    name: str

    def enabled(self) -> bool: ...

    def search(self, query: str, market: Market) -> list[Offer]: ...
