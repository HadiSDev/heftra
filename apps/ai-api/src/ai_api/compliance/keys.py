"""What makes a term the question a judgement answered."""
from __future__ import annotations

import hashlib
import json

from web_api.db.models import AgreementTerm

JUDGE_VERSION = 2


def term_key(term: AgreementTerm, buyer: str = "") -> str:
    """A digest of what the scope judge reads of the term and the buyer, and of its prompt's
    version; a change to any of them asks again."""
    payload = json.dumps([JUDGE_VERSION, term.kind, _norm(term.scope), _norm(term.conditions),
                          _norm(term.item), _norm(term.unit), _norm(buyer)])
    return hashlib.sha256(payload.encode()).hexdigest()


def _norm(value: str | None) -> str:
    return " ".join((value or "").lower().split())
