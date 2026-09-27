"""Suggesting the spend categories a term's scope covers, from the company's tree."""
from __future__ import annotations

import logging
from collections.abc import Callable

from sqlmodel import Session, select

from web_api.db.models import Company, SpendCategory

from .. import config
from ..rag.embedding import embed

logger = logging.getLogger("ai_api.agreements")

Suggest = Callable[[str], list[str]]
EmbedFn = Callable[[list[str]], list[list[float]]]


def category_suggester(session: Session, company_id: str, *,
                       embed_fn: EmbedFn = embed) -> Suggest:
    """A function giving the ids of the categories whose paths are closest to a scope."""
    paths = _category_paths(session, company_id)
    if not paths:
        return _suggest_nothing
    try:
        vectors = embed_fn(list(paths.values()))
    except Exception as error:  # noqa: BLE001
        logger.warning("agreement: the spend tree could not be embedded: %s", error)
        return _suggest_nothing
    ids = list(paths)

    def suggest(scope: str) -> list[str]:
        try:
            query = embed_fn([scope])[0]
        except Exception as error:  # noqa: BLE001
            logger.warning("agreement: no category suggestions for %r: %s", scope, error)
            return []
        scored = sorted(
            ((sum(a * b for a, b in zip(vector, query)), node_id)
             for node_id, vector in zip(ids, vectors)),
            key=lambda pair: pair[0], reverse=True,
        )
        return [node_id for _, node_id in scored[:config.AGREEMENT_SCOPE_CATEGORIES]]

    return suggest


def _suggest_nothing(scope: str) -> list[str]:
    return []


def _category_paths(session: Session, company_id: str) -> dict[str, str]:
    """Each category of the company's tree by id, as its path from the root."""
    company = session.get(Company, company_id)
    if company is None or company.spend_tree_id is None:
        return {}
    nodes = {node.id: node for node in session.exec(
        select(SpendCategory).where(SpendCategory.spend_tree_id == company.spend_tree_id)
    ).all()}
    paths: dict[str, str] = {}
    for node_id, node in nodes.items():
        names: list[str] = []
        current: SpendCategory | None = node
        while current is not None:
            names.append(current.name)
            current = nodes.get(current.parent_id) if current.parent_id else None
        paths[node_id] = " / ".join(reversed(names))
    return paths
