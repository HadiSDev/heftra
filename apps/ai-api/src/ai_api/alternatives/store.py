"""Writing an item's alternatives over its last search's, keeping every review."""
from __future__ import annotations

from datetime import datetime

from sqlmodel import Session, select

from web_api.db.models import (
    AlternativeMatch,
    AlternativeReviewStatus,
    CompanyItem,
    DismissReason,
    ItemAlternative,
)

from .matching.verdicts import AttributeComparison
from .saving import Saving
from .sources.found import Found


class AlternativeStore:
    """The item's alternatives as the search found them: reviewed ones are left as they are and
    not raised again, open ones are updated, and open ones not found again go."""

    def __init__(self, session: Session, item: CompanyItem, currency: str) -> None:
        self._session = session
        self._item = item
        self._currency = currency
        self._existing = {(alternative.source, alternative.ref_key): alternative
                          for alternative in session.exec(select(ItemAlternative).where(
                              ItemAlternative.item_id == item.id)).all()}
        self._kept: set[tuple[str, str]] = set()

    def reviewed(self, found: Found) -> bool:
        """Whether a person reviewed this alternative, or ruled its product not equivalent."""
        existing = self._existing.get((found.source.value, found.ref_key))
        if existing is not None and existing.review_status != AlternativeReviewStatus.OPEN.value:
            return True
        return found.product_id is not None and found.product_id in self._not_equivalent()

    def put(self, found: Found, match: AlternativeMatch, comparison: list[AttributeComparison],
            saving: Saving, notes: list[dict], now: datetime) -> None:
        key = (found.source.value, found.ref_key)
        alternative = self._existing.get(key) or ItemAlternative(
            company_id=self._item.company_id, item_id=self._item.id, source=found.source.value,
            ref_key=found.ref_key, name=found.name, unit_price=found.unit_price,
            currency=self._currency, saving_percent=saving.percent, found_at=now)
        alternative.match = match.value
        alternative.name = found.name
        alternative.unit_price = found.unit_price
        alternative.currency = self._currency
        alternative.saving_percent = saving.percent
        alternative.saving_yearly = saving.yearly
        alternative.comparison = [entry.stored() for entry in comparison]
        alternative.origin = {**found.origin, "product_id": found.product_id}
        alternative.agreement_notes = notes
        alternative.found_at = now
        self._session.add(alternative)
        self._kept.add(key)

    def drop_unfound(self, sources: set[str]) -> None:
        """Delete the open alternatives of the searched sources that weren't found again."""
        for key, alternative in self._existing.items():
            if alternative.source in sources and key not in self._kept \
                    and alternative.review_status == AlternativeReviewStatus.OPEN.value:
                self._session.delete(alternative)

    def _not_equivalent(self) -> set[str]:
        return {alternative.origin.get("product_id") for alternative in self._existing.values()
                if alternative.dismiss_reason == DismissReason.NOT_EQUIVALENT.value
                and alternative.origin.get("product_id")}

