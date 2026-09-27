"""Suggesting the spend categories a term covers."""
from __future__ import annotations

from sqlmodel import Session

from agreement_books import Books, embed
from ai_api import config
from ai_api.agreements.scope_categories import category_suggester


def test_without_a_tree_nothing_is_suggested(engine):
    with Session(engine) as s:
        books = Books(s)
        assert category_suggester(s, books.company.id, embed_fn=embed)("IT equipment") == []


def test_the_categories_closest_to_the_scope_are_suggested(engine, monkeypatch):
    monkeypatch.setattr(config, "AGREEMENT_SCOPE_CATEGORIES", 1)
    with Session(engine) as s:
        books = Books(s)
        tree = books.tree("Coffee", "Office Equipment")

        suggest = category_suggester(s, books.company.id, embed_fn=embed)

        assert suggest("IT equipment and accessories") == [tree["Office Equipment"].id]


def test_an_embedding_error_suggests_nothing(engine):
    def broken(texts):
        raise RuntimeError("model missing")

    with Session(engine) as s:
        books = Books(s)
        books.tree("Office Equipment")
        assert category_suggester(s, books.company.id, embed_fn=broken)("IT equipment") == []
