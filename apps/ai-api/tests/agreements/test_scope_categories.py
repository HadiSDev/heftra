"""Suggesting the spend categories a term covers."""
from __future__ import annotations

from sqlmodel import Session

from ai_api import config
from ai_api.agreements import scope_categories
from ai_api.agreements.scope_categories import category_suggester


def test_without_a_tree_nothing_is_suggested(engine, make_tenant):
    company_id = make_tenant()["company_id"]

    with Session(engine) as s:
        assert category_suggester(s, company_id)("IT equipment") == []


def test_the_closest_categories_are_suggested(engine, make_tenant, monkeypatch):
    company_id = make_tenant()["company_id"]
    monkeypatch.setattr(config, "AGREEMENT_SCOPE_CATEGORIES", 2)
    monkeypatch.setattr(scope_categories, "index_tree", lambda session, company_id: None)
    asked = []

    def retriever(company):
        def retrieve(query, top_k):
            asked.append((query, top_k))
            return [{"spend_category_id": "hardware"}, {"name": "no id"}]
        return retrieve

    monkeypatch.setattr(scope_categories, "retriever_for", retriever)

    with Session(engine) as s:
        assert category_suggester(s, company_id)("IT equipment") == ["hardware"]
    assert asked == [("IT equipment", 2)]


def test_a_retrieval_error_suggests_nothing(engine, make_tenant, monkeypatch):
    company_id = make_tenant()["company_id"]
    monkeypatch.setattr(scope_categories, "index_tree", lambda session, company_id: None)

    def broken(company):
        def retrieve(query, top_k):
            raise ConnectionError("qdrant down")
        return retrieve

    monkeypatch.setattr(scope_categories, "retriever_for", broken)

    with Session(engine) as s:
        assert category_suggester(s, company_id)("IT equipment") == []
