"""Writing the demo company from scratch, and removing it."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date, datetime, timezone

from sqlmodel import Session, select

from web_api.db.models import Company, EmissionFactorSet, Organization, PipelineRunKind, User
from web_api.db.session import engine

from .catalog.agreements import AGREEMENTS
from .catalog.lookup import sector_codes
from .generation.planned import PlannedInvoice
from .generation.purchases import PurchasePlanner
from .ids import COMPANY_ID
from .settings import ORGANIZATION_ID
from .writers.agreements.records import AgreementWriter
from .writers.agreements.storage import discard_pdfs, upload_pdfs
from .writers.fx_cache import warm_rates
from .writers.items.alternatives import AlternativeWriter
from .writers.items.stored_items import write_items
from .writers.ledger.books import Books
from .writers.ledger.writer import LedgerWriter
from .writers.pipeline import summarize, write_runs
from .writers.setup.company import write_company, write_erp
from .writers.setup.sectors import active_sectors
from .writers.setup.tree import write_tree
from .writers.setup.vendors import write_vendors
from .writers.teardown import remove_company, remove_vendors


class SeedingRefused(RuntimeError):
    """The database lacks what the demo is written against."""


@dataclass
class SeedOutcome:
    invoices: int = 0
    lines: int = 0
    items: int = 0
    alternatives: int = 0
    findings: int = 0
    findings_by_kind: dict[str, int] = field(default_factory=dict)
    storage_error: str | None = None
    days_without_rate: int = 0


def seed(*, reset: bool, warm_fx: bool) -> SeedOutcome:
    """Replace the demo company's rows with freshly written ones; with `reset`, its suppliers
    are deleted and written again too."""
    now = datetime.now(timezone.utc)
    plan = PurchasePlanner().plan()
    outcome = SeedOutcome(invoices=len(plan), lines=sum(len(invoice.lines) for invoice in plan))
    with Session(engine) as session:
        uploader = _uploader(session)
        remove_company(session)
        if reset:
            remove_vendors(session)
        vendors = write_vendors(session)
        leaves = write_tree(session)
        write_company(session, now)
        books = Books(vendors=vendors, leaves=leaves, accounts=write_erp(session),
                      sectors=active_sectors(session, sector_codes()))
        runs = write_runs(session, now)
        LedgerWriter(session, books).write(plan)
        session.commit()

        items = write_items(session, date.today(), now)
        agreements = AgreementWriter(session, books, plan, uploader, now).write(AGREEMENTS)
        alternatives = AlternativeWriter(session, items, now).write()
        _summarize_runs(session, runs, outcome, plan, len(items), len(alternatives),
                        agreements.findings)
        session.commit()

        outcome.items = len(items)
        outcome.alternatives = len(alternatives)
        outcome.findings = agreements.findings
        outcome.findings_by_kind = dict(agreements.by_kind)
        if warm_fx:
            outcome.days_without_rate = warm_rates(session, {invoice.on for invoice in plan},
                                                   _factor_currency(session))
    outcome.storage_error = upload_pdfs(agreements.files)
    return outcome


def remove() -> bool:
    """Delete the demo company, its spend tree and its suppliers; returns whether it existed."""
    with Session(engine) as session:
        existed = session.get(Company, COMPANY_ID) is not None
        keys = remove_company(session)
        remove_vendors(session)
        session.commit()
    discard_pdfs(keys)
    return existed


def _uploader(session: Session) -> str:
    """The organization's first member, who uploaded and reviewed the agreements."""
    if session.get(Organization, ORGANIZATION_ID) is None:
        raise SeedingRefused(f"Organization {ORGANIZATION_ID} doesn't exist.")
    user = session.exec(select(User).where(User.organization_id == ORGANIZATION_ID)
                        .order_by(User.created_at, User.id)).first()
    if user is None:
        raise SeedingRefused(f"Organization {ORGANIZATION_ID} has no members.")
    return user.id


def _factor_currency(session: Session) -> str:
    factor_set = session.exec(
        select(EmissionFactorSet).where(EmissionFactorSet.active == True)  # noqa: E712
    ).one()
    return factor_set.currency


def _summarize_runs(session: Session, runs: dict, outcome: SeedOutcome,
                    plan: list[PlannedInvoice], items: int, alternatives: int,
                    findings: int) -> None:
    entries = sum(len(invoice.lines) + 2 for invoice in plan)
    summarize(session, runs[PipelineRunKind.SYNC.value],
              {"invoices": outcome.invoices, "lines": outcome.lines, "entries": entries})
    summarize(session, runs[PipelineRunKind.CATEGORIZE.value], {"categorized": outcome.lines})
    summarize(session, runs[PipelineRunKind.MATCH_EMISSIONS.value], {"matched": outcome.lines})
    summarize(session, runs[PipelineRunKind.ANALYSE_AGREEMENTS.value],
              {"agreements": len(AGREEMENTS), "findings": findings, "similarity": True,
               "capped_terms": 0, "unjudged": 0})
    summarize(session, runs[PipelineRunKind.SCAN_ALTERNATIVES.value],
              {"items": items, "searched": items, "alternatives": alternatives,
               "similarity": True})

