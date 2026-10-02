"""How much of an agreement a run redoes: everything, or what changed since its last run."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from web_api.db.models import Agreement, AgreementTerm

from .. import config


@dataclass(frozen=True)
class RunScope:
    """`last_run` is when the agreement's last complete run started; `since` is that less a
    margin for line writes not yet committed then. Both are None for a full run."""

    last_run: datetime | None
    since: datetime | None

    @property
    def full(self) -> bool:
        return self.since is None

    def since_for(self, term: AgreementTerm) -> datetime | None:
        """None when the term's lines must all be redone: a full run, or a term confirmed or
        edited after the last run started."""
        if self.since is None or self.last_run is None:
            return None
        changed = max(_aware(term.created_at), _aware(term.updated_at) or _aware(term.created_at))
        return None if changed > self.last_run else self.since


def run_scope(agreement: Agreement) -> RunScope:
    """Full for a first run or when one was requested; otherwise from the watermark."""
    last_run = _aware(agreement.analysed_from)
    if agreement.full_analysis or last_run is None:
        return RunScope(None, None)
    return RunScope(last_run, watermark(agreement))


def watermark(agreement: Agreement) -> datetime | None:
    """When the agreement's last complete run started, less a margin for writes that were not yet
    committed then; None before its first run."""
    started = _aware(agreement.analysed_from)
    if started is None:
        return None
    return started - timedelta(minutes=config.AGREEMENT_WATERMARK_MARGIN_MINUTES)


def _aware(moment: datetime | None) -> datetime | None:
    if moment is None:
        return None
    return moment if moment.tzinfo else moment.replace(tzinfo=timezone.utc)
