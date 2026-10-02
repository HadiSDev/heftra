"""The sentence embedding every index here shares, loaded once."""
from __future__ import annotations

import torch
from sentence_transformers import SentenceTransformer

from .. import config

_model: SentenceTransformer | None = None


def embed(texts: list[str]) -> list[list[float]]:
    global _model
    if _model is None:
        _model = _load()
    return _model.encode(texts, normalize_embeddings=True).tolist()


def query_text(text: str) -> str:
    """A search text as the model expects it, with its query prefix."""
    return f"{config.EMBEDDING_QUERY_PREFIX}{text}"


def _load() -> SentenceTransformer:
    if torch.cuda.is_available():
        model = SentenceTransformer(config.EMBEDDING_MODEL,
                                    model_kwargs={"torch_dtype": torch.float16})
    else:
        model = SentenceTransformer(config.EMBEDDING_MODEL)
    model.max_seq_length = min(model.max_seq_length, config.EMBEDDING_MAX_TOKENS)
    return model
