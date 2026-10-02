"""What switching to an alternative would break under the company's agreements."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from urllib.parse import urlparse

from sqlmodel import Session, col, select

from web_api.company_context import business_context
from web_api.compliance.commitments import commitment_progress
from web_api.db.models import (
    Agreement,
    AgreementScopeJudgement,
    AgreementStatus,
    AgreementTerm,
    AgreementTermKind,
    AgreementTermStatus,
    AlternativeSource,
    Company,
    CompanyItem,
    Vendor,
)

from ..compliance.keys import term_key
from .sources.found import Found

BINDING_KINDS = (AgreementTermKind.PREFERRED_SUPPLIER.value,
                 AgreementTermKind.VOLUME_COMMITMENT.value)


@dataclass(frozen=True)
class Binding:
    """A confirmed term of an active agreement the item is judged in scope of."""

    agreement: Agreement
    term: AgreementTerm
    supplier: str
    supplier_host: str | None
    behind: bool


def item_bindings(session: Session, company: Company, item: CompanyItem,
                  today: date) -> list[Binding]:
    """The preferred-supplier and commitment terms the item falls under, by the in-scope
    rulings of the terms as they now read."""
    buyer = business_context(company)
    bindings: list[Binding] = []
    for agreement in session.exec(select(Agreement).where(
            Agreement.company_id == company.id,
            Agreement.status == AgreementStatus.ACTIVE.value)).all():
        terms = [term for term in session.exec(select(AgreementTerm).where(
            AgreementTerm.agreement_id == agreement.id,
            AgreementTerm.status == AgreementTermStatus.CONFIRMED.value,
            col(AgreementTerm.kind).in_(BINDING_KINDS))).all()
            if _in_scope(session, term, buyer, item.item_key)]
        if not terms:
            continue
        behind = _behind_terms(session, agreement, company, today)
        vendor = session.get(Vendor, agreement.vendor_id) if agreement.vendor_id else None
        supplier = vendor.name if vendor else (agreement.supplier_name or "the supplier")
        host = _host(vendor.website) if vendor and vendor.website else None
        bindings += [Binding(agreement, term, supplier, host, term.id in behind)
                     for term in terms]
    return bindings


def agreement_notes(found: Found, bindings: list[Binding]) -> list[dict]:
    """What buying the alternative would break: another supplier under a preferred-supplier
    term, or more spend away from a commitment that is behind."""
    notes: list[dict] = []
    if found.source == AlternativeSource.BENCHMARK:
        return notes
    for binding in bindings:
        if _from_supplier(found, binding):
            continue
        title = binding.agreement.title or "the agreement"
        if binding.term.kind == AgreementTermKind.PREFERRED_SUPPLIER.value:
            notes.append(_note(binding, "off_contract",
                               f"Buying it here would be off contract under {title}, which "
                               f"requires {binding.supplier} for {binding.term.scope}."))
        elif binding.behind:
            notes.append(_note(binding, "commitment_behind",
                               f"The commitment under {title} is behind; buying this "
                               f"elsewhere would put it further behind."))
    return notes


def _in_scope(session: Session, term: AgreementTerm, buyer: str, item_key: str) -> bool:
    return session.exec(select(AgreementScopeJudgement.id).where(
        AgreementScopeJudgement.term_id == term.id,
        AgreementScopeJudgement.term_key == term_key(term, buyer),
        AgreementScopeJudgement.question_key == item_key,
        AgreementScopeJudgement.in_scope == True,  # noqa: E712
    )).first() is not None


def _behind_terms(session: Session, agreement: Agreement, company: Company,
                  today: date) -> set[str]:
    return {progress.term_id for progress in commitment_progress(
        session, agreement, company.base_currency, today)
        if progress.spent < progress.target_to_date}


def _from_supplier(found: Found, binding: Binding) -> bool:
    if found.vendor_id is not None:
        return found.vendor_id == binding.agreement.vendor_id
    if found.seller_host and binding.supplier_host:
        return _bare(found.seller_host) == _bare(binding.supplier_host)
    return False


def _note(binding: Binding, kind: str, text: str) -> dict:
    return {"kind": kind, "agreement_id": binding.agreement.id, "term_id": binding.term.id,
            "text": text}


def _host(website: str) -> str | None:
    return urlparse(website if "://" in website else f"https://{website}").hostname


def _bare(host: str) -> str:
    return host.lower().removeprefix("www.")
