"""A company's items embedded once and searched within dates."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest
from qdrant_client import QdrantClient

from agreement_books import embed
from ai_api.items.index import ItemIndex, SimilarityUnavailable
from ai_api.items.item import Item


def _item(key: str, name: str, first: date, last: date, category: str = "c1") -> Item:
    return Item(key=key, item_name=name, description=None, unit="piece", category_id=category,
                category_path=(), vendor_id="v1", vendor_name="Proshop", lines=1,
                spend=Decimal(100), unit_price=None, first_on=first, last_on=last)


class CountingEmbed:
    def __init__(self) -> None:
        self.texts = 0

    def __call__(self, texts: list[str]) -> list[list[float]]:
        self.texts += len(texts)
        return embed(texts)


@pytest.fixture
def index():
    counting = CountingEmbed()
    return ItemIndex(QdrantClient(location=":memory:"), counting), counting


def test_only_new_items_are_embedded(index):
    index, counting = index
    laptop = _item("k1", "Dell laptop", date(2026, 1, 1), date(2026, 3, 1))

    assert index.ensure("co", [laptop]) == 1
    assert index.ensure("co", [laptop, _item("k2", "Coffee", date(2026, 1, 1),
                                              date(2026, 1, 1))]) == 1
    assert counting.texts == 2


def test_search_finds_similar_items_within_the_dates(index):
    index, _ = index
    index.ensure("co", [
        _item("old", "Dell laptop", date(2024, 1, 1), date(2024, 6, 1)),
        _item("new", "HP laptop", date(2026, 1, 1), date(2026, 3, 1)),
        _item("coffee", "Coffee beans", date(2026, 1, 1), date(2026, 3, 1)),
    ])

    hits = index.search("co", "laptop", start=date(2025, 1, 1), end=None, threshold=0.5,
                        limit=10)

    assert [hit.key for hit in hits] == ["new"]


def test_a_later_line_moves_an_item_into_the_dates(index):
    index, counting = index
    index.ensure("co", [_item("k1", "Dell laptop", date(2024, 1, 1), date(2024, 6, 1))])

    index.ensure("co", [_item("k1", "Dell laptop", date(2024, 1, 1), date(2026, 2, 1))])

    assert counting.texts == 1
    assert [hit.key for hit in index.search("co", "laptop", start=date(2026, 1, 1), end=None,
                                            threshold=0.5, limit=10)] == ["k1"]


def test_search_can_keep_to_categories(index):
    index, _ = index
    index.ensure("co", [_item("a", "Dell laptop", date(2026, 1, 1), date(2026, 1, 1), "c1"),
                        _item("b", "HP laptop", date(2026, 1, 1), date(2026, 1, 1), "c2")])

    hits = index.search("co", "laptop", start=None, end=None, threshold=0.5, limit=10,
                        category_ids=["c2"])

    assert [hit.key for hit in hits] == ["b"]


def test_an_unreachable_index_is_reported():
    class Broken:
        def get_collections(self):
            raise ConnectionError("qdrant down")

    index = ItemIndex(Broken(), embed)

    with pytest.raises(SimilarityUnavailable):
        index.ensure("co", [_item("k1", "Dell laptop", date(2026, 1, 1), date(2026, 1, 1))])
    with pytest.raises(SimilarityUnavailable):
        index.search("co", "laptop", start=None, end=None, threshold=0.5, limit=10)
