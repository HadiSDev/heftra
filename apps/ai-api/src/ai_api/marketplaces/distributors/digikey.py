"""Digi-Key's Product Information API (v4): a keyword search, priced in the market's currency."""
from __future__ import annotations

import time
from decimal import Decimal

import httpx

from ... import config
from ..market import Market
from ..offer import Offer, PriceBreak
from ..source import ConnectorFailed

TOKEN_URL = "https://api.digikey.com/v1/oauth2/token"
SEARCH_URL = "https://api.digikey.com/products/v4/search/keyword"
TIMEOUT_S = 20
LIMIT = 5


class DigiKey:
    name = "digikey"

    def __init__(self, client_id: str | None = None, client_secret: str | None = None,
                 client: httpx.Client | None = None) -> None:
        self._id = client_id if client_id is not None else config.DIGIKEY_CLIENT_ID
        self._secret = client_secret if client_secret is not None else \
            config.DIGIKEY_CLIENT_SECRET
        self._client = client or httpx.Client(timeout=TIMEOUT_S)
        self._token: str | None = None
        self._expires = 0.0

    def enabled(self) -> bool:
        return bool(self._id and self._secret)

    def search(self, query: str, market: Market) -> list[Offer]:
        try:
            response = self._client.post(SEARCH_URL, json={"Keywords": query, "Limit": LIMIT},
                                         headers=self._headers(market))
            response.raise_for_status()
            products = response.json().get("Products") or []
        except (httpx.HTTPError, ValueError) as error:
            raise ConnectorFailed(f"Digi-Key: {error}") from error
        return [offer for product in products
                if (offer := _offer(product, market.currency)) is not None]

    def _headers(self, market: Market) -> dict[str, str]:
        return {"Authorization": f"Bearer {self._bearer()}", "X-DIGIKEY-Client-Id": self._id,
                "X-DIGIKEY-Locale-Site": market.country, "X-DIGIKEY-Locale-Language": "en",
                "X-DIGIKEY-Locale-Currency": market.currency}

    def _bearer(self) -> str:
        if self._token is None or time.monotonic() >= self._expires:
            response = self._client.post(TOKEN_URL, data={
                "client_id": self._id, "client_secret": self._secret,
                "grant_type": "client_credentials"})
            response.raise_for_status()
            body = response.json()
            self._token = body["access_token"]
            self._expires = time.monotonic() + int(body.get("expires_in", 600)) - 60
        return self._token


def _offer(product: dict, currency: str) -> Offer | None:
    variations = product.get("ProductVariations") or []
    pricing = (variations[0].get("StandardPricing") or []) if variations else []
    breaks = tuple(sorted(PriceBreak(int(entry["BreakQuantity"]), Decimal(str(entry["UnitPrice"])))
                          for entry in pricing if entry.get("UnitPrice") is not None))
    unit = product.get("UnitPrice")
    price = breaks[0].price if breaks else (Decimal(str(unit)) if unit else None)
    url = product.get("ProductUrl")
    if price is None or not url:
        return None
    description = product.get("Description") or {}
    return Offer(seller="Digi-Key",
                 title=description.get("ProductDescription") or
                 product.get("ManufacturerProductNumber", ""),
                 url=url, price=price, currency=currency, vat_included=False,
                 description=description.get("DetailedDescription") or "",
                 part_number=product.get("ManufacturerProductNumber"),
                 brand=(product.get("Manufacturer") or {}).get("Name"), price_breaks=breaks,
                 availability=str(product.get("QuantityAvailable"))
                 if product.get("QuantityAvailable") is not None else None)
