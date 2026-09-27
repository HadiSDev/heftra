"""The lines worth asking the judge about for a term."""
from __future__ import annotations

from collections.abc import Callable, Sequence

from sqlmodel import Session, select

from web_api.db.models import AgreementTerm, SpendCategory

from .. import config
from .lines import AnalysedLine

EmbedFn = Callable[[list[str]], list[list[float]]]


class LineVectors:
    """Each line's embedding, computed once per run."""

    def __init__(self, lines: Sequence[AnalysedLine], embed_fn: EmbedFn) -> None:
        self._embed_fn = embed_fn
        self._vectors: dict[str, list[float]] = {}
        if lines:
            texts = [line.text or "(no description)" for line in lines]
            self._vectors = dict(zip((line.line_id for line in lines), embed_fn(texts)))

    def similarity(self, line_id: str, query: list[float]) -> float:
        vector = self._vectors.get(line_id)
        if vector is None:
            return 0.0
        return sum(a * b for a, b in zip(vector, query))

    def embed(self, text: str) -> list[float]:
        return self._embed_fn([text])[0]


def descendants(session: Session, category_ids: list[str]) -> set[str]:
    """The categories and every category below them."""
    wanted = set(category_ids)
    if not wanted:
        return wanted
    children: dict[str, list[str]] = {}
    for node_id, parent_id in session.exec(select(SpendCategory.id, SpendCategory.parent_id)):
        if parent_id is not None:
            children.setdefault(parent_id, []).append(node_id)
    frontier = list(wanted)
    while frontier:
        for child in children.get(frontier.pop(), []):
            if child not in wanted:
                wanted.add(child)
                frontier.append(child)
    return wanted


def candidates(term: AgreementTerm, lines: Sequence[AnalysedLine], vectors: LineVectors,
               categories: set[str]) -> list[AnalysedLine]:
    """Lines in the term's categories, then the most similar others above the threshold."""
    by_category = [line for line in lines if line.category_id in categories]
    chosen = {line.line_id for line in by_category}
    query = vectors.embed(_term_text(term))
    scored = sorted(
        ((vectors.similarity(line.line_id, query), line) for line in lines
         if line.line_id not in chosen),
        key=lambda pair: pair[0], reverse=True,
    )
    room = max(0, config.AGREEMENT_CANDIDATES_MAX - len(by_category))
    similar = [line for score, line in scored[:room] if score >= config.AGREEMENT_SIMILARITY_MIN]
    return by_category + similar


def _term_text(term: AgreementTerm) -> str:
    return " — ".join(part for part in (term.item, term.scope) if part)
