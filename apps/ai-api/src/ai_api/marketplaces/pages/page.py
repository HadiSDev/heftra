"""A fetched web page."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Page:
    url: str
    html: str
    markdown: str
    links: tuple[str, ...] = field(default_factory=tuple)


Fetch = Callable[[list[str]], list[Page]]
