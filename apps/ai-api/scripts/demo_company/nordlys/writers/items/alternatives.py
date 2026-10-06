"""The alternatives the last scan found, stored as the search stores them."""
from __future__ import annotations

from datetime import datetime, timedelta
from decimal import ROUND_HALF_UP, Decimal

from sqlmodel import Session

from ai_api.alternatives.saving import saving
from web_api.db.models import CompanyItem, ItemAlternative, Vendor
from web_api.specs.specification import Specification

from ...catalog import company as profile
from ...catalog.agreements import AGREEMENTS, PREFERRED_SUPPLIER
from ...catalog.alternatives import ALTERNATIVES, BENCHMARK, HISTORY
from ...catalog.shapes import AlternativeSpec
from ...catalog.suppliers import by_key
from ...ids import COMPANY_ID, demo_id
from ...settings import CURRENCY
from .stored_items import ItemKey

PRICE_PLACES = Decimal("0.000001")
LOWEST_QUARTILE_SHARE = Decimal("0.955")
OPEN = "open"
SAME = "same"


class NotCheaper(ValueError):
    """An alternative the catalog lists doesn't save enough on the item it is for."""


class AlternativeWriter:
    def __init__(self, session: Session, items: dict[ItemKey, CompanyItem], now: datetime) -> None:
        self._session = session
        self._items = items
        self._now = now
        self._suppliers = by_key()

    def write(self) -> list[ItemAlternative]:
        """Add every alternative of the catalog; the caller commits."""
        written = [self._alternative(spec) for spec in ALTERNATIVES]
        self._session.add_all(written)
        self._session.flush()
        return written

    def _alternative(self, spec: AlternativeSpec) -> ItemAlternative:
        item = self._items[(spec.supplier, spec.product)]
        item_spec = Specification.model_validate(item.spec)
        if spec.source == HISTORY:
            other = self._items[(spec.cheaper_supplier, spec.product)]
            price = other.unit_price
            ref_key = f"item:{other.id}"
            origin = self._history_origin(other)
        else:
            price = (item.unit_price * Decimal(spec.price_ratio)).quantize(PRICE_PLACES,
                                                                          ROUND_HALF_UP)
            ref_key = self._ref_key(spec, item)
            origin = self._found_origin(spec, price)
        found = saving(item.unit_price, price, item.quantity)
        if found is None:
            raise NotCheaper(f"{spec.supplier}/{spec.product} from {spec.source} saves too little")
        return ItemAlternative(
            id=demo_id("alternative", f"{spec.supplier}:{spec.product}:{spec.source}"),
            company_id=COMPANY_ID, item_id=item.id, source=spec.source, match=spec.match,
            ref_key=ref_key, name=spec.name or item_spec.name, unit_price=price,
            currency=CURRENCY, saving_yearly=found.yearly, saving_percent=found.percent,
            comparison=self._comparison(spec, item_spec), origin={**origin, "product_id": None},
            agreement_notes=self._agreement_notes(spec), review_status=OPEN,
            found_at=self._now - timedelta(days=spec.found_days_ago))

    def _history_origin(self, other: CompanyItem) -> dict:
        vendor = self._session.get(Vendor, other.vendor_id)
        return {"supplier": vendor.name, "vendor_id": vendor.id, "company": profile.NAME,
                "company_id": COMPANY_ID, "item_id": other.id, "item_name": other.item_name,
                "last_bought_on": other.last_bought_on.isoformat()}

    def _found_origin(self, spec: AlternativeSpec, price: Decimal) -> dict:
        if spec.source == BENCHMARK:
            lowest = (price * LOWEST_QUARTILE_SHARE).quantize(PRICE_PLACES, ROUND_HALF_UP)
            return {**spec.origin, "median": str(price), "lowest_quartile": str(lowest)}
        seen = self._now - timedelta(days=spec.found_days_ago)
        return {**spec.origin, "title": spec.name, "seen_at": seen.isoformat()}

    @staticmethod
    def _ref_key(spec: AlternativeSpec, item: CompanyItem) -> str:
        if spec.source == BENCHMARK:
            return f"benchmark:specification:{item.spec_signature}"
        return f"offer:{spec.origin['connector']}:{spec.origin['url']}"

    @staticmethod
    def _comparison(spec: AlternativeSpec, item_spec: Specification) -> list[dict]:
        rows = []
        for attribute in item_spec.attributes:
            verdict, candidate, reason = spec.verdicts.get(
                attribute.name, (SAME, attribute.value, ""))
            rows.append({"name": attribute.name, "item": attribute.value,
                         "candidate": candidate, "verdict": verdict, "reason": reason})
        return rows

    def _agreement_notes(self, spec: AlternativeSpec) -> list[dict]:
        """Buying a product bound to an agreement's supplier anywhere else is off contract."""
        if spec.source == BENCHMARK:
            return []
        notes = []
        for agreement in AGREEMENTS:
            if agreement.supplier == spec.cheaper_supplier or agreement.supplier != spec.supplier:
                continue
            supplier_name = self._suppliers[agreement.supplier].name
            for term in agreement.terms:
                if term.kind == PREFERRED_SUPPLIER and spec.product in term.products:
                    notes.append({
                        "kind": "off_contract",
                        "agreement_id": demo_id("agreement", agreement.key),
                        "term_id": demo_id("agreement-term", f"{agreement.key}:{term.key}"),
                        "text": (f"Buying it here would be off contract under "
                                 f"{agreement.title}, which requires {supplier_name} for "
                                 f"{term.scope}.")})
        return notes
