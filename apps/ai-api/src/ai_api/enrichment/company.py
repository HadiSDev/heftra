"""What a company does, researched from its website for the models that read its spend."""
from __future__ import annotations

import logging
from collections.abc import Callable
from datetime import datetime, timezone
from functools import partial

from sqlalchemy.engine import Engine
from sqlmodel import Session, col, select

from web_api.company_context import HUMAN, RESEARCHED
from web_api.db.models import Company

from .. import config
from .site.crawler import crawl_site
from .site.fetch import fetch_site
from .supplier_profile import SupplierProfile, describe_supplier

logger = logging.getLogger("ai_api.enrichment")

Describe = Callable[[str, str | None, str | None], SupplierProfile]


def default_describe() -> Describe:
    """Describe from the company's own site when crawling is on, from search snippets otherwise."""
    if config.SUPPLIER_CRAWL_ENABLED:
        return partial(describe_supplier, crawl_fn=partial(crawl_site, fetch_site=fetch_site))
    return describe_supplier


def companies_to_research(session: Session, limit: int) -> list[Company]:
    """Active companies with a website that have neither a description nor a research attempt."""
    return list(session.exec(
        select(Company).where(
            Company.is_active == True,  # noqa: E712
            col(Company.website).is_not(None),
            col(Company.description).is_(None),
            col(Company.researched_at).is_(None),
        ).order_by(col(Company.created_at), col(Company.id)).limit(limit)
    ).all())


def research_pending_companies(engine: Engine, *, describe: Describe | None = None,
                               limit: int | None = None) -> bool:
    """Research the companies waiting for it; returns whether there were any."""
    if not config.COMPANY_RESEARCH_ENABLED:
        return False
    with Session(engine) as session:
        waiting = [(company.id, company.name, company.country_code, company.website)
                   for company in companies_to_research(
                       session, limit or config.COMPANY_RESEARCH_BATCH)]
    if not waiting:
        return False
    describe = describe or default_describe()
    for company_id, name, country_code, website in waiting:
        try:
            profile = describe(name, country_code, website)
        except Exception:  # noqa: BLE001
            logger.exception("company %s could not be researched", company_id)
            profile = SupplierProfile("", website)
        _store(engine, company_id, website, profile.description.strip())
    return True


def _store(engine: Engine, company_id: str, website: str | None, description: str) -> None:
    with Session(engine) as session:
        company = session.get(Company, company_id)
        if company is None or company.website != website or company.description_source == HUMAN:
            return
        company.researched_at = datetime.now(timezone.utc)
        if description:
            company.description = description
            company.description_source = RESEARCHED
        session.add(company)
        session.commit()
    logger.info("company %s: %s", company_id,
                "described from its website" if description else "nothing found to describe it")
