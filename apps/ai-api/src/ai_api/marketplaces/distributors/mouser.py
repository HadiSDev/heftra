"""Mouser's Search API (v1): a keyword search, which also finds part numbers."""
from __future__ import annotations

import httpx

from ... import config
from ..market import Market
from ..offer import Offer, PriceBreak
from ..pages.prices import parse_price
from ..source import ConnectorFailed

BASE = "https://api.mouser.com/api/v1"
TIMEOUT_S = 20
RECORDS = 5


class Mouser:
    name = "mouser"

    def __init__(self, api_key: str | None = None, client: httpx.Client | None = None) -> None:
        self._key = api_key if api_key is not None else config.MOUSER_API_KEY
        self._client = client or httpx.Client(timeout=TIMEOUT_S)

    def enabled(self) -> bool:
        return bool(self._key)

    def search(self, query: str, market: Market) -> list[Offer]:
        try:
            response = self._client.post(
                f"{BASE}/search/keyword", params={"apiKey": self._key},
                json={"SearchByKeywordRequest": {"keyword": query, "records": RECORDS,
                                                 "startingRecord": 0}})
            response.raise_for_status()
            body = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise ConnectorFailed(f"Mouser: {error}") from error
        if body.get("Errors"):
            raise ConnectorFailed(f"Mouser: {body['Errors']}")
        parts = (body.get("SearchResults") or {}).get("Parts") or []
        return [offer for part in parts if (offer := _offer(part)) is not None]


def _offer(part: dict) -> Offer | None:
    breaks = sorted(
        ((PriceBreak(int(entry["Quantity"]), price), entry.get("Currency"))
         for entry in part.get("PriceBreaks") or []
         if (price := parse_price(entry.get("Price"))) is not None),
        key=lambda pair: pair[0])
    if not breaks or not breaks[0][1] or not part.get("ProductDetailUrl"):
        return None
    return Offer(seller="Mouser", title=part.get("Description") or part["ManufacturerPartNumber"],
                 url=part["ProductDetailUrl"], price=breaks[0][0].price,
                 currency=breaks[0][1], vat_included=False,
                 description=part.get("Description") or "",
                 part_number=part.get("ManufacturerPartNumber"),
                 brand=part.get("Manufacturer"),
                 price_breaks=tuple(entry for entry, _ in breaks),
                 availability=part.get("Availability"))
