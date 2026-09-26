"""The sentence embedding every index here shares, loaded once."""
from __future__ import annotations

from sentence_transformers import SentenceTransformer

from .. import config

_model: SentenceTransformer | None = None


def embed(texts: list[str]) -> list[list[float]]:
    global _model
    if _model is None:
        _model = SentenceTransformer(config.EMBEDDING_MODEL)
    return _model.encode(texts, normalize_embeddings=True).tolist()
