"""Every company's specified items in one Qdrant collection, searched for similar specifications
within an organization or across the others."""
from __future__ import annotations

import uuid
from collections.abc import Callable, Iterable
from typing import NamedTuple

from qdrant_client import QdrantClient
from qdrant_client.http import models

from web_api.specs.specification import Specification

from .. import config
from ..items.index import SimilarityUnavailable
from ..rag.collections import collection_exists, model_collection
from ..rag.embedding import embed

Embed = Callable[[list[str]], list[list[float]]]
COLLECTION = "item_specs"
EMBED_BATCH = 256
LOOKUP_BATCH = 500
_NAMESPACE = uuid.UUID("8c1d6b2e-4f3a-4e5d-b7c9-1a2b3c4d5e6f")


class SpecEntry(NamedTuple):
    item_id: str
    company_id: str
    organization_id: str
    product_id: str | None
    spec: Specification


class SpecHit(NamedTuple):
    item_id: str
    organization_id: str
    score: float


class SpecIndex:
    """Embeds each item's specification, again when it changes, and finds the nearest ones of
    the same class and pricing unit."""

    def __init__(self, client: QdrantClient, embed_fn: Embed = embed) -> None:
        self._client = client
        self._embed = embed_fn

    @classmethod
    def connect(cls, embed_fn: Embed = embed) -> SpecIndex:
        return cls(QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT,
                                prefer_grpc=False), embed_fn)

    def ensure(self, entries: Iterable[SpecEntry]) -> int:
        """Embed the entries that are new or whose specification changed; returns how many."""
        try:
            return self._ensure(list(entries))
        except Exception as error:  # noqa: BLE001
            raise SimilarityUnavailable(str(error)) from error

    def search(self, spec: Specification, *, limit: int, threshold: float,
               organization_id: str | None = None,
               other_than_organization_id: str | None = None) -> list[SpecHit]:
        """Items of the specification's class and pricing unit nearest it, best first, within
        one organization or outside one."""
        try:
            if not collection_exists(self._client, _collection()):
                return []
            points = self._client.query_points(
                _collection(), query=self._embed([spec.text])[0], limit=limit, with_payload=True,
                score_threshold=threshold,
                query_filter=_filter(spec, organization_id, other_than_organization_id),
            ).points
        except Exception as error:  # noqa: BLE001
            raise SimilarityUnavailable(str(error)) from error
        return [SpecHit(point.payload["item_id"], point.payload["organization_id"], point.score)
                for point in points if point.payload]

    def _ensure(self, entries: list[SpecEntry]) -> int:
        if not entries:
            return 0
        stored = self._digests(entries) if collection_exists(self._client, _collection()) else {}
        changed = [entry for entry in entries
                   if stored.get(_point_id(entry.item_id)) != entry.spec.digest]
        for begin in range(0, len(changed), EMBED_BATCH):
            batch = changed[begin:begin + EMBED_BATCH]
            vectors = self._embed([entry.spec.text for entry in batch])
            if not collection_exists(self._client, _collection()):
                self._client.create_collection(_collection(), vectors_config=models.VectorParams(
                    size=len(vectors[0]), distance=models.Distance.COSINE))
            self._client.upsert(_collection(), points=[
                models.PointStruct(id=_point_id(entry.item_id), vector=vector, payload={
                    "item_id": entry.item_id, "company_id": entry.company_id,
                    "organization_id": entry.organization_id, "product_id": entry.product_id,
                    "item_class": entry.spec.item_class.value,
                    "pricing_unit": entry.spec.pricing_unit.value,
                    "digest": entry.spec.digest})
                for entry, vector in zip(batch, vectors)
            ])
        return len(changed)

    def _digests(self, entries: list[SpecEntry]) -> dict[str, str]:
        ids = [_point_id(entry.item_id) for entry in entries]
        digests: dict[str, str] = {}
        for begin in range(0, len(ids), LOOKUP_BATCH):
            for point in self._client.retrieve(_collection(), ids=ids[begin:begin + LOOKUP_BATCH],
                                               with_payload=["digest"], with_vectors=False):
                digests[str(point.id)] = (point.payload or {}).get("digest")
        return digests


def _point_id(item_id: str) -> str:
    return str(uuid.uuid5(_NAMESPACE, item_id))


def _filter(spec: Specification, organization_id: str | None,
            other_than: str | None) -> models.Filter:
    must = [
        models.FieldCondition(key="item_class",
                              match=models.MatchValue(value=spec.item_class.value)),
        models.FieldCondition(key="pricing_unit",
                              match=models.MatchValue(value=spec.pricing_unit.value)),
    ]
    if organization_id is not None:
        must.append(models.FieldCondition(key="organization_id",
                                          match=models.MatchValue(value=organization_id)))
    must_not = []
    if other_than is not None:
        must_not.append(models.FieldCondition(key="organization_id",
                                              match=models.MatchValue(value=other_than)))
    return models.Filter(must=must, must_not=must_not or None)


def _collection() -> str:
    return model_collection(COLLECTION)
