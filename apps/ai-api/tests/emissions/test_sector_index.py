"""Sectors are embedded once per classification and searched by meaning."""
from __future__ import annotations

from uuid import uuid4

from qdrant_client import QdrantClient

from ai_api import config
from ai_api.emissions.sector_index import SectorIndex
from web_api.db.models import EmissionSector

VOCAB = ["hosting", "software", "flight", "legal"]


def fake_embed(texts):
    return [[float(text.lower().count(word)) + 0.01 for word in VOCAB] for text in texts]


def _sector(code, name, description):
    return EmissionSector(id=str(uuid4()), classification="ceda-bea", code=code, name=name,
                          description=description)


SECTORS = [
    _sector("518200", "Data processing, hosting", "Hosting and data centres for hosting."),
    _sector("511200", "Software publishers", "Publishing software."),
    _sector("481000", "Air transportation", "Passenger flight services."),
]


def _index(embed=fake_embed) -> tuple[SectorIndex, QdrantClient]:
    client = QdrantClient(location=":memory:")
    return SectorIndex(client, embed), client


def test_the_nearest_sectors_come_first():
    index, _ = _index()
    index.ensure("ceda-bea", SECTORS)

    hits = index.search("ceda-bea", "server hosting", limit=2)

    assert [hit.code for hit in hits][0] == "518200"
    assert hits[0].summary == "Hosting and data centres for hosting."
    assert len(hits) == 2


def test_an_index_that_holds_the_sectors_is_not_rebuilt():
    calls = []

    def counting_embed(texts):
        calls.append(len(texts))
        return fake_embed(texts)

    index, _ = _index(counting_embed)
    index.ensure("ceda-bea", SECTORS)
    index.ensure("ceda-bea", SECTORS)

    assert calls == [3]


def test_a_classification_never_built_finds_nothing():
    index, _ = _index()

    assert index.search("ceda-bea", "hosting", limit=5) == []


def test_searches_carry_the_query_prefix_and_documents_do_not(monkeypatch):
    monkeypatch.setattr(config, "EMBEDDING_QUERY_PREFIX", "query: ")
    seen = []

    def recording_embed(texts):
        seen.extend(texts)
        return fake_embed(texts)

    index, _ = _index(recording_embed)
    index.ensure("ceda-bea", SECTORS)
    index.search("ceda-bea", "server hosting", limit=1)

    assert seen[-1] == "query: server hosting"
    assert not any(text.startswith("query: ") for text in seen[:-1])


def test_another_model_builds_collections_of_its_own(monkeypatch):
    index, client = _index()
    index.ensure("ceda-bea", SECTORS)
    monkeypatch.setattr(config, "EMBEDDING_MODEL", "Snowflake/snowflake-arctic-embed-m-v2.0")

    assert index.search("ceda-bea", "hosting", limit=5) == []
    index.ensure("ceda-bea", SECTORS)
    names = sorted(collection.name for collection in client.get_collections().collections)
    assert names[-1] == "emission_sectors_ceda-bea__snowflake_arctic_embed_m_v2_0"
    assert len(names) == 2
