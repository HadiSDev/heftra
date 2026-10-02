"""The items worth asking the judge about for a term: by category in SQL, then by similarity."""
from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date

from sqlmodel import Session, select

from web_api.db.models import AgreementTerm, SpendCategory

from .. import config
from ..items.grouping import company_items
from ..items.index import ItemIndex, SimilarityUnavailable
from ..items.item import Item


@dataclass(frozen=True)
class Window:
    """Where a term looks: the company, the agreement's validity, and the items it may consider
    (None for all of them)."""

    company_id: str
    start: date | None
    end: date | None
    keys: frozenset[str] | None = None


@dataclass
class Candidates:
    items: list[Item] = field(default_factory=list)
    capped: bool = False


class Similarity:
    """The item index for one run, switched off for the rest of it once it can't be reached."""

    def __init__(self, index: ItemIndex | None) -> None:
        self._index = index
        self.available = index is not None

    def ensure(self, company_id: str, items: list[Item]) -> int:
        if not self.available or self._index is None:
            return 0
        try:
            return self._index.ensure(company_id, items)
        except SimilarityUnavailable:
            self.available = False
            return 0

    def search(self, window: Window, text: str, limit: int) -> list[str]:
        if not self.available or self._index is None:
            return []
        try:
            hits = self._index.search(window.company_id, text, start=window.start,
                                      end=window.end, threshold=config.AGREEMENT_SIMILARITY_MIN,
                                      limit=limit)
        except SimilarityUnavailable:
            self.available = False
            return []
        return [hit.key for hit in hits]


def descendants(session: Session, category_ids: Iterable[str]) -> set[str]:
    """The categories and every category below them."""
    wanted = set(category_ids)
    if not wanted:
        return wanted
    children: dict[str, list[str]] = {}
    for node_id, parent_id in session.exec(select(SpendCategory.id, SpendCategory.parent_id)):
        if parent_id is not None:
            children.setdefault(parent_id, []).append(node_id)
    frontier = list(wanted)
    while frontier:
        for child in children.get(frontier.pop(), []):
            if child not in wanted:
                wanted.add(child)
                frontier.append(child)
    return wanted


def term_candidates(session: Session, term: AgreementTerm, window: Window,
                    categories: set[str], similarity: Similarity) -> Candidates:
    """The term's candidate items, most spend first, capped at `AGREEMENT_CANDIDATES_MAX`."""
    cap = config.AGREEMENT_CANDIDATES_MAX
    keys = list(window.keys) if window.keys is not None else None
    by_category = company_items(session, window.company_id, start=window.start, end=window.end,
                                category_ids=categories, keys=keys, limit=cap + 1) \
        if categories else []
    similar_keys = [key for key in similarity.search(window, term_text(term), cap + 1)
                    if window.keys is None or key in window.keys]
    chosen = {item.key: item for item in by_category}
    missing = [key for key in similar_keys if key not in chosen]
    for item in company_items(session, window.company_id, start=window.start, end=window.end,
                              keys=missing) if missing else []:
        chosen[item.key] = item
    ranked = sorted(chosen.values(), key=lambda item: item.spend, reverse=True)
    return Candidates(ranked[:cap], capped=len(ranked) > cap)


def term_text(term: AgreementTerm) -> str:
    return " — ".join(part for part in (term.item, term.scope) if part)
