"""What a company does: its website, and a description researched from it or written by a manager."""
from __future__ import annotations

from fastapi import HTTPException, status

from web_api.db.models import Company
from web_api.website import site_root

RESEARCHED = "web"
HUMAN = "human"


def apply_context(company: Company, changes: dict) -> None:
    """Set the website and description sent, keeping what a manager wrote over research."""
    if "website" in changes:
        _set_website(company, changes["website"])
    if "description" in changes:
        _set_description(company, changes["description"])


def business_context(company: Company) -> str:
    """The company and what it does, for a model to read; its name alone when undescribed."""
    if company.description:
        return f"{company.name}: {company.description}"
    return company.name


def _set_website(company: Company, website: str | None) -> None:
    root = site_root(website) if website else None
    if website and root is None:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                            detail="That is not a website address.")
    if root == company.website:
        return
    company.website = root
    company.researched_at = None
    if company.description_source != HUMAN:
        company.description = None
        company.description_source = None


def _set_description(company: Company, description: str | None) -> None:
    text = (description or "").strip()
    if text:
        company.description = text
        company.description_source = HUMAN
        return
    company.description = None
    company.description_source = None
    company.researched_at = None
