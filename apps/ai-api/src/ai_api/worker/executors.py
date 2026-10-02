"""One executor per run kind, each returning the summary the run records."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from sqlmodel import Session

from web_api.db.models import PipelineRunKind

from ..alternatives.run import ItemNotFound, find_alternatives, scan_alternatives
from ..categorization.company import categorize_company
from ..compliance.run import analyse_company
from ..config import get_llm
from ..documents import runner as documents_runner
from ..emissions.lines import match_company
from ..rag.embedding import embed
from ..sync import runner as sync_runner
from ..sync.integrations import connected_integrations



@dataclass(frozen=True)
class RunRequest:
    """What a run asks: its company, and the parameters of its kind."""

    company_id: str
    params: dict = field(default_factory=dict)


Executor = Callable[[Session, RunRequest], dict]

_SYNC_COUNTS = ("invoices", "lines", "documents_queued", "standin_lines", "lines_withdrawn")


class RunFailed(RuntimeError):
    """The stage ran but could not do what the run asked."""


def _sync_summary(results: list[dict]) -> dict:
    summary: dict = {"integrations": len(results), "categorized": 0, "categorization_failed": 0}
    for key in _SYNC_COUNTS:
        summary[key] = sum(result.get(key, 0) for result in results)
    for result in results:
        categorization = result.get("categorization", {})
        summary["categorized"] += categorization.get("categorized", 0)
        summary["categorization_failed"] += categorization.get("failed", 0)
        if "skipped" in categorization:
            summary["categorization_skipped"] = categorization["skipped"]
    return summary


def sync(session: Session, request: RunRequest) -> dict:
    """Sync every connected integration of the company, as the sync CLI does."""
    integrations = connected_integrations(session, company_id=request.company_id)
    if not integrations:
        raise RunFailed("the company has no connected ERP integration")

    results: list[dict] = []
    for integration in integrations:
        results.extend(sync_runner.run_sync(integration_id=integration.id).values())

    errors = [result["error"] for result in results if result.get("status") == "error"]
    if errors:
        raise RunFailed("; ".join(errors))
    return _sync_summary(results)


def read_documents(session: Session, request: RunRequest) -> dict:
    """Read the company's pending documents, as the documents CLI does."""
    return documents_runner.run_documents(company_id=request.company_id)


def categorize(session: Session, request: RunRequest) -> dict:
    """Categorize the company's uncategorized lines without contacting the ERP."""
    stats = categorize_company(session, request.company_id)
    if "unavailable" in stats:
        raise RunFailed(f"the categorizer is unavailable: {stats['unavailable']}")
    return stats


def match_emissions(session: Session, request: RunRequest) -> dict:
    """Match the company's lines to emission sectors, as the emissions CLI does."""
    return match_company(session, request.company_id)


def analyse_agreements(session: Session, request: RunRequest) -> dict:
    """Check the company's spend lines against its active agreements' confirmed terms."""
    return analyse_company(session, request.company_id, ask=_ask(), embed_fn=embed)


def find_item_alternatives(session: Session, request: RunRequest) -> dict:
    """Search the alternatives of the item the run names."""
    item_id = request.params.get("item_id")
    if not item_id:
        raise RunFailed("the run names no item")
    try:
        return find_alternatives(session, request.company_id, item_id, ask=_ask(),
                                 embed_fn=embed)
    except ItemNotFound as error:
        raise RunFailed(str(error)) from error


def scan_company_alternatives(session: Session, request: RunRequest) -> dict:
    """Search the alternatives of the company's largest-spend items that are due."""
    return scan_alternatives(session, request.company_id, ask=_ask(), embed_fn=embed)


def _ask() -> Callable[[str], str]:
    llm = get_llm()
    return lambda prompt: llm.call([{"role": "user", "content": prompt}])


EXECUTORS: dict[str, Executor] = {
    PipelineRunKind.SYNC.value: sync,
    PipelineRunKind.READ_DOCUMENTS.value: read_documents,
    PipelineRunKind.CATEGORIZE.value: categorize,
    PipelineRunKind.MATCH_EMISSIONS.value: match_emissions,
    PipelineRunKind.ANALYSE_AGREEMENTS.value: analyse_agreements,
    PipelineRunKind.FIND_ALTERNATIVES.value: find_item_alternatives,
    PipelineRunKind.SCAN_ALTERNATIVES.value: scan_company_alternatives,
}


def execute(session: Session, kind: str, company_id: str, params: dict | None = None) -> dict:
    """Run the executor for ``kind`` and return its summary."""
    executor = EXECUTORS.get(kind)
    if executor is None:
        raise RunFailed(f"unknown run kind {kind!r}")
    return executor(session, RunRequest(company_id, params or {}))
