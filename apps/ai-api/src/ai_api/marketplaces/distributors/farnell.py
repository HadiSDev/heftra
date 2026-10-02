"""Farnell's element14 Product Search API: the market's store, prices without VAT."""
from __future__ import annotations

from decimal import Decimal

import httpx

from ... import config
from ..market import Market
from ..offer import Offer, PriceBreak
from ..source import ConnectorFailed

URL = "https://api.element14.com/catalog/products"
TIMEOUT_S = 20
RESULTS = 5
STORES = {"DK": "dk.farnell.com", "SE": "se.farnell.com", "NO": "no.farnell.com",
          "FI": "fi.farnell.com", "DE": "de.farnell.com", "NL": "nl.farnell.com",
          "GB": "uk.farnell.com"}
_RETURNS = ("keywordSearchReturn", "manufacturerPartNumberSearchReturn",
            "premierFarnellPartNumberReturn")


class Farnell:
    name = "farnell"

    def __init__(self, api_key: str | None = None, client: httpx.Client | None = None) -> None:
        self._key = api_key if api_key is not None else config.FARNELL_API_KEY
        self._client = client or httpx.Client(timeout=TIMEOUT_S)

    def enabled(self) -> bool:
        return bool(self._key)

    def search(self, query: str, market: Market) -> list[Offer]:
        store = STORES.get(market.country)
        if store is None:
            return []
        try:
            response = self._client.get(URL, params={
                "term": f"any:{query}", "storeInfo.id": store,
                "resultsSettings.offset": 0, "resultsSettings.numberOfResults": RESULTS,
                "resultsSettings.responseGroup": "large",
                "callInfo.responseDataFormat": "JSON", "callInfo.apiKey": self._key})
            response.raise_for_status()
            body = response.json()
        except (httpx.HTTPError, ValueError) as error:
            raise ConnectorFailed(f"Farnell: {error}") from error
        found = next((body[key] for key in _RETURNS if key in body), {})
        return [offer for product in found.get("products") or []
                if (offer := _offer(product, store, market.currency)) is not None]


def _offer(product: dict, store: str, currency: str) -> Offer | None:
    breaks = tuple(sorted(PriceBreak(int(entry["from"]), Decimal(str(entry["cost"])))
                          for entry in product.get("prices") or [] if entry.get("cost")))
    if not breaks or not product.get("sku"):
        return None
    pack = int(product.get("packSize") or 1)
    unit = (product.get("unitOfMeasure") or "").lower()
    return Offer(seller="Farnell", title=product.get("displayName") or product["sku"],
                 url=f"https://{store}/dp/{product['sku']}", price=breaks[0].price,
                 currency=currency, vat_included=False,
                 description=product.get("displayName") or "",
                 pack=f"{pack} {unit}".strip() if pack > 1 else None,
                 part_number=product.get("translatedManufacturerPartNumber"),
                 brand=product.get("brandName"), price_breaks=breaks,
                 availability=str((product.get("stock") or {}).get("level"))
                 if (product.get("stock") or {}).get("level") is not None else None)
