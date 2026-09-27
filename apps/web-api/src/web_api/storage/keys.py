"""Where each kind of upload is stored."""
from __future__ import annotations

from uuid import uuid4


def agreement_key(company_id: str, agreement_id: str) -> str:
    return f"companies/{company_id}/agreements/{agreement_id}/{uuid4().hex}.pdf"
