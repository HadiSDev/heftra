"""The key of the item a line bought: what it is, how it is counted, its category and supplier."""
from __future__ import annotations

import hashlib
import json
import re

_SPACES = re.compile(r"\s+")


def item_key(item_name: str | None, description: str | None, unit: str | None,
             category_id: str | None, vendor_id: str | None) -> str:
    """A digest that is equal for lines buying the same thing from the same supplier."""
    payload = json.dumps([_norm(item_name), _norm(description), _norm(unit), category_id or "",
                          vendor_id or ""], ensure_ascii=False)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def item_text(item_name: str | None, description: str | None) -> str:
    """What the item is called, for a person or a model to read."""
    name = (item_name or "").strip()
    detail = (description or "").strip()
    if name and detail and detail.casefold() != name.casefold():
        return f"{name} — {detail}"
    return name or detail or "(no description)"


def _norm(value: str | None) -> str:
    return _SPACES.sub(" ", (value or "").strip()).casefold()
