"""Specifications indexed across companies and searched within or outside an organization."""
from __future__ import annotations

import pytest
from qdrant_client import QdrantClient

from agreement_books import embed
from ai_api.items.index import SimilarityUnavailable
from ai_api.specs.index import SpecEntry, SpecIndex
from ai_api.specs.specification import Specification
from spec_stub import spec


def _spec(name: str, **fields) -> Specification:
    return Specification.model_validate(spec(name, **fields))


class CountingEmbed:
    def __init__(self) -> None:
        self.texts = 0

    def __call__(self, texts: list[str]) -> list[list[float]]:
        self.texts += len(texts)
        return embed(texts)


@pytest.fixture
def index():
    counting = CountingEmbed()
    return SpecIndex(QdrantClient(location=":memory:"), counting), counting


def test_equivalent_items_are_found_across_companies(index):
    index, _ = index
    bar = {"item_class": "material", "product_type": "round bar steel", "pricing_unit": "kg"}
    index.ensure([SpecEntry("i1", "c1", "o1", None, _spec("round bar S235 20mm", **bar)),
                  SpecEntry("i2", "c2", "o2", None, _spec("round bar S235 20mm steel", **bar)),
                  SpecEntry("i3", "c3", "o3", None, _spec("laptop dock"))])

    hits = index.search(_spec("round bar S235 20mm", **bar), limit=10, threshold=0.0)

    assert {(hit.item_id, hit.organization_id) for hit in hits} == {("i1", "o1"), ("i2", "o2")}
    others = index.search(_spec("round bar S235 20mm", **bar), limit=10, threshold=0.0,
                          other_than_organization_id="o1")
    assert [hit.item_id for hit in others] == ["i2"]
    own = index.search(_spec("round bar S235 20mm", **bar), limit=10, threshold=0.0,
                       organization_id="o1")
    assert [hit.item_id for hit in own] == ["i1"]


def test_a_specification_is_embedded_again_only_when_it_changes(index):
    index, counting = index
    laptop = _spec("ThinkPad laptop")
    index.ensure([SpecEntry("i1", "c1", "o1", None, laptop)])

    assert index.ensure([SpecEntry("i1", "c1", "o1", None, laptop)]) == 0
    assert index.ensure([SpecEntry("i1", "c1", "o1", None, _spec("ThinkPad laptop 32GB"))]) == 1
    assert counting.texts == 2


def test_an_unreachable_index_says_so():
    class Broken:
        def collection_exists(self, name):
            raise ConnectionError("down")

        def get_collections(self):
            raise ConnectionError("down")

    with pytest.raises(SimilarityUnavailable):
        SpecIndex(Broken(), embed).search(_spec("laptop"), limit=5, threshold=0.0)
