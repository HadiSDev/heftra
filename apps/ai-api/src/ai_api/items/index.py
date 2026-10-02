"""A company's items in Qdrant: embedded once, then searched by similarity within dates."""
from __future__ import annotations

import uuid
from collections.abc import Callable, Iterable
from datetime import date
from typing import NamedTuple

from qdrant_client import QdrantClient
from qdrant_client.http import models

from .. import config
from ..rag.collections import collection_exists, model_collection
from ..rag.embedding import embed, query_text
from .item import Item

Embed = Callable[[list[str]], list[list[float]]]
EMBED_BATCH = 256
LOOKUP_BATCH = 500
_NAMESPACE = uuid.UUID("5f4e2a1c-8b7d-4c3e-9a6f-2d1b0c9e8f7a")


class SimilarityUnavailable(RuntimeError):
    """The item index can't be reached."""


class ItemHit(NamedTuple):
    key: str
    score: float


class ItemIndex:
    """Embeds each company's items once, and finds the ones nearest a text."""

    def __init__(self, client: QdrantClient, embed_fn: Embed = embed) -> None:
        self._client = client
        self._embed = embed_fn

    @classmethod
    def connect(cls, embed_fn: Embed = embed) -> ItemIndex:
        return cls(QdrantClient(host=config.QDRANT_HOST, port=config.QDRANT_PORT,
                                prefer_grpc=False), embed_fn)

    def ensure(self, company_id: str, items: Iterable[Item]) -> int:
        """Embed the items the collection lacks and refresh the dates of the rest; returns how
        many were embedded."""
        try:
            return self._ensure(_collection(company_id), list(items))
        except Exception as error:  # noqa: BLE001
            raise SimilarityUnavailable(str(error)) from error

    def search(self, company_id: str, text: str, *, start: date | None, end: date | None,
               threshold: float, limit: int,
               category_ids: Iterable[str] | None = None) -> list[ItemHit]:
        """The items most similar to `text` with lines within the dates, best first."""
        name = _collection(company_id)
        try:
            if not text.strip() or not collection_exists(self._client, name):
                return []
            points = self._client.query_points(
                name, query=self._embed([query_text(text)])[0], limit=limit, with_payload=True,
                score_threshold=threshold,
                query_filter=_filter(start, end, category_ids),
            ).points
        except Exception as error:  # noqa: BLE001
            raise SimilarityUnavailable(str(error)) from error
        return [ItemHit(point.payload["item_key"], point.score) for point in points
                if point.payload]

    def _ensure(self, name: str, items: list[Item]) -> int:
        if not items:
            return 0
        stored = self._stored(name, items) if collection_exists(self._client, name) else {}
        missing = [item for item in items if _point_id(item.key) not in stored]
        for item in items:
            dates = stored.get(_point_id(item.key))
            if dates is not None and dates != _dates(item):
                self._client.set_payload(name, payload=_dates(item), points=[_point_id(item.key)])
        for begin in range(0, len(missing), EMBED_BATCH):
            batch = missing[begin:begin + EMBED_BATCH]
            vectors = self._embed([item.text for item in batch])
            if not collection_exists(self._client, name):
                self._client.create_collection(name, vectors_config=models.VectorParams(
                    size=len(vectors[0]), distance=models.Distance.COSINE))
            self._client.upsert(name, points=[
                models.PointStruct(id=_point_id(item.key), vector=vector, payload={
                    "item_key": item.key, "category_id": item.category_id,
                    "vendor_id": item.vendor_id, **_dates(item)})
                for item, vector in zip(batch, vectors)
            ])
        return len(missing)

    def _stored(self, name: str, items: list[Item]) -> dict[str, dict]:
        ids = [_point_id(item.key) for item in items]
        stored: dict[str, dict] = {}
        for begin in range(0, len(ids), LOOKUP_BATCH):
            for point in self._client.retrieve(name, ids=ids[begin:begin + LOOKUP_BATCH],
                                               with_payload=["first_on", "last_on"],
                                               with_vectors=False):
                payload = point.payload or {}
                stored[str(point.id)] = {"first_on": payload.get("first_on"),
                                         "last_on": payload.get("last_on")}
        return stored


def _collection(company_id: str) -> str:
    return model_collection(f"spend_items_{company_id}")


def _point_id(key: str) -> str:
    return str(uuid.uuid5(_NAMESPACE, key))


def _dates(item: Item) -> dict:
    return {"first_on": item.first_on.toordinal() if item.first_on else None,
            "last_on": item.last_on.toordinal() if item.last_on else None}


def _filter(start: date | None, end: date | None,
            category_ids: Iterable[str] | None) -> models.Filter | None:
    must: list[models.FieldCondition] = []
    if start is not None:
        must.append(models.FieldCondition(key="last_on",
                                          range=models.Range(gte=start.toordinal())))
    if end is not None:
        must.append(models.FieldCondition(key="first_on",
                                          range=models.Range(lte=end.toordinal())))
    if category_ids is not None:
        must.append(models.FieldCondition(key="category_id",
                                          match=models.MatchAny(any=list(category_ids))))
    return models.Filter(must=must) if must else None
