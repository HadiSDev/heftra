"""A vector index over one classification's emission sectors."""
from __future__ import annotations

import textwrap
from collections.abc import Callable
from typing import NamedTuple

from qdrant_client import QdrantClient
from qdrant_client.http import models

from web_api.db.models import EmissionSector

from .. import config
from ..rag.collections import collection_exists, recreate_collection
from ..rag.embedding import embed

SUMMARY_CHARS = 220

Embed = Callable[[list[str]], list[list[float]]]


class SectorHit(NamedTuple):
    sector_id: str
    code: str
    name: str
    summary: str


def summary_of(sector: EmissionSector) -> str:
    """The start of the sector's description, short enough to list several of."""
    return textwrap.shorten(sector.description or "", SUMMARY_CHARS, placeholder=" …")


class SectorIndex:
    """Embeds each classification's sectors once, and finds the ones nearest a query."""

    def __init__(self, client: QdrantClient, embed_fn: Embed = embed) -> None:
        self._client = client
        self._embed = embed_fn

    @classmethod
    def connect(cls) -> SectorIndex:
        return cls(QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT,
                                prefer_grpc=False))

    def ensure(self, classification: str, sectors: list[EmissionSector]) -> None:
        """Build the classification's collection unless it already holds these sectors."""
        name = _collection(classification)
        if not sectors:
            return
        if collection_exists(self._client, name) and self._client.count(name).count == len(sectors):
            return
        vectors = self._embed([f"{sector.name}: {sector.description or ''}" for sector in sectors])
        recreate_collection(self._client, name, len(vectors[0]))
        self._client.upsert(name, points=[
            models.PointStruct(id=sector.id, vector=vector, payload={
                "sector_id": sector.id, "code": sector.code, "name": sector.name,
                "summary": summary_of(sector),
            })
            for sector, vector in zip(sectors, vectors)
        ])

    def search(self, classification: str, query: str, limit: int) -> list[SectorHit]:
        name = _collection(classification)
        if not query.strip() or not collection_exists(self._client, name):
            return []
        points = self._client.query_points(
            name, query=self._embed([query])[0], limit=limit, with_payload=True
        ).points
        return [
            SectorHit(point.payload["sector_id"], point.payload["code"], point.payload["name"],
                      point.payload["summary"])
            for point in points
            if point.payload
        ]


def _collection(classification: str) -> str:
    return f"emission_sectors_{classification}"
