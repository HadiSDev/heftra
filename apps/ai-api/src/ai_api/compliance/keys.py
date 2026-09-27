"""What makes a term the question a judgement answered."""
from __future__ import annotations

import hashlib
import json

from web_api.db.models import AgreementTerm


def term_key(term: AgreementTerm) -> str:
    """A digest of the fields the scope judge reads; editing any of them asks again."""
    payload = json.dumps([term.kind, _norm(term.scope), _norm(term.conditions), _norm(term.item),
                          _norm(term.unit)])
    return hashlib.sha256(payload.encode()).hexdigest()


def _norm(value: str | None) -> str:
    return " ".join((value or "").lower().split())
