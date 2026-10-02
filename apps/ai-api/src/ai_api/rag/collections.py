"""Qdrant collection housekeeping shared by the indexes."""
from __future__ import annotations

import re

from qdrant_client import QdrantClient
from qdrant_client.http.models import Distance, VectorParams

from .. import config


def model_collection(name: str) -> str:
    """`name` for the configured embedding model, so another model gets collections of its own
    instead of searching vectors it didn't make."""
    model = config.EMBEDDING_MODEL.rsplit("/", 1)[-1].lower()
    return f"{name}__{re.sub(r'[^a-z0-9]+', '_', model).strip('_')}"


def collection_exists(client: QdrantClient, name: str) -> bool:
    return any(c.name == name for c in client.get_collections().collections)


def recreate_collection(client: QdrantClient, name: str, vector_size: int) -> None:
    """Drop ``name`` if it exists and create it empty for ``vector_size`` vectors."""
    if collection_exists(client, name):
        client.delete_collection(name)
    client.create_collection(
        name,
        vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE),
    )
