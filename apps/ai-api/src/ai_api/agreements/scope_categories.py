"""Suggesting the spend categories a term's scope covers, from the company's tree."""
from __future__ import annotations

import logging
from collections.abc import Callable

from sqlmodel import Session

from web_api.db.models import Company

from .. import config
from ..categorization.tree import index_tree, retriever_for

logger = logging.getLogger("ai_api.agreements")

Suggest = Callable[[str], list[str]]


def category_suggester(session: Session, company_id: str) -> Suggest:
    """A function giving the closest categories' ids for a scope, or none without a tree."""
    index_tree(session, company_id)
    retrieve = retriever_for(session.get(Company, company_id))

    def suggest(scope: str) -> list[str]:
        try:
            hits = retrieve(scope, config.AGREEMENT_SCOPE_CATEGORIES)
        except Exception as error:  # noqa: BLE001
            logger.warning("agreement: no category suggestions for %r: %s", scope, error)
            return []
        return [hit["spend_category_id"] for hit in hits if hit.get("spend_category_id")]

    return suggest
