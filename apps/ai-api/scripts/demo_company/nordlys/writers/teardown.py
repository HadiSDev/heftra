"""Removing the demo company and everything scoped to it, and nothing else."""
from __future__ import annotations

from sqlmodel import Session, col, delete, select

from web_api.company_deletion import delete_company
from web_api.db.models import (
    Agreement,
    AgreementTerm,
    AgreementTermSpend,
    Company,
    SpendCategory,
    SpendTree,
    Vendor,
)

from ..catalog.suppliers import SUPPLIERS
from ..ids import COMPANY_ID, TREE_ID, demo_id


def remove_company(session: Session) -> list[str]:
    """Delete the demo company with the app's own company deletion, and its spend tree; returns
    the storage keys of its agreement files. The caller commits."""
    keys: list[str] = []
    company = session.get(Company, COMPANY_ID)
    if company is not None:
        _remove_term_spend(session)
        keys = delete_company(session, company).stored_keys
        session.flush()
    _remove_tree(session)
    return keys


def remove_vendors(session: Session) -> int:
    """Delete the demo's suppliers from the shared supplier table; the caller commits."""
    ids = [demo_id("vendor", spec.key) for spec in SUPPLIERS]
    found = session.exec(select(Vendor).where(col(Vendor.id).in_(ids))).all()
    for vendor in found:
        session.delete(vendor)
    session.flush()
    return len(found)


def _remove_term_spend(session: Session) -> None:
    """The company deletion leaves the terms' monthly spend, which would block deleting them."""
    terms = (select(AgreementTerm.id)
             .join(Agreement, Agreement.id == AgreementTerm.agreement_id)
             .where(Agreement.company_id == COMPANY_ID))
    session.exec(delete(AgreementTermSpend).where(col(AgreementTermSpend.term_id).in_(terms)))


def _remove_tree(session: Session) -> None:
    categories = session.exec(
        select(SpendCategory).where(SpendCategory.spend_tree_id == TREE_ID)
    ).all()
    for category in sorted(categories, key=lambda node: node.depth, reverse=True):
        session.delete(category)
        session.flush()
    tree = session.get(SpendTree, TREE_ID)
    if tree is not None:
        session.delete(tree)
        session.flush()
