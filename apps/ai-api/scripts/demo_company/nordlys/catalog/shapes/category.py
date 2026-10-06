"""A node of the demo company's spend tree and an account of its chart of accounts."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CategorySpec:
    """`path` runs from the root; a leaf has a `code`."""

    path: tuple[str, ...]
    code: str | None = None
    description: str | None = None


@dataclass(frozen=True)
class AccountSpec:
    """An expense account is synced; VAT and payables accounts are not."""

    code: str
    name: str
    kind: str
    synced: bool
