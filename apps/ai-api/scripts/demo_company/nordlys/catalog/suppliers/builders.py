"""Writing a supplier and its offers briefly."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from ..pricing import quantity
from ..shapes import Billing, OfferSpec, PricePoint, ProductSpec, SupplierSpec
from ..vat_numbers import fictional_vat


def offer(product: ProductSpec, prices: tuple[PricePoint, ...], low: str = "1", high: str = "1",
          *, step: str = "1", weight: float = 1.0, jitter: float = 0.0,
          discount: str | None = None, discount_since: date | None = None,
          discount_share: float = 0.0) -> OfferSpec:
    return OfferSpec(product=product, prices=prices, quantity=quantity(low, high),
                     step=Decimal(step), weight=weight, price_jitter=jitter,
                     discount_percent=Decimal(discount) if discount else None,
                     discount_since=discount_since, discount_share=discount_share)


def supplier(key: str, name: str, city: str, account: str, prefix: str, description: str,
             offers: tuple[OfferSpec, ...], *, per_month: float = 1.0,
             lines: tuple[int, int] = (1, 3), seasonal: bool = True,
             billing: Billing = Billing.ORDERS, first_day: date | None = None) -> SupplierSpec:
    """A supplier on its own .example domain, with a VAT number no real company has."""
    return SupplierSpec(key=key, name=name, vat_number=fictional_vat(key), city=city,
                        website=f"https://{key}.example", description=description,
                        account=account, invoice_prefix=prefix, offers=offers,
                        invoices_per_month=per_month, lines_per_invoice=lines, seasonal=seasonal,
                        billing=billing, first_day=first_day)
