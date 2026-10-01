"""The agreement's defined words, written out in the scopes that use them."""
from __future__ import annotations

import re
from dataclasses import dataclass, replace

from .models import ReadDefinition
from .pages import AgreementPage
from .terms import MIN_QUOTE_CHARS, DraftTerm, comparable


@dataclass(frozen=True)
class Definition:
    term: str
    meaning: str


def checked_definitions(read: list[ReadDefinition], page: AgreementPage) -> list[Definition]:
    """The definitions whose meaning is found on the page they were read from."""
    found = []
    for definition in read:
        term = definition.term.strip().strip("\"'“”")
        meaning = definition.meaning.strip().rstrip(".;, ")
        wanted = comparable(meaning)
        if not term or len(wanted) < MIN_QUOTE_CHARS:
            continue
        if page.text is None:
            if page.image is not None:
                found.append(Definition(term, meaning))
            continue
        if wanted in comparable(page.text):
            found.append(Definition(term, meaning))
    return found


def with_definitions(terms: list[DraftTerm], definitions: list[Definition]) -> list[DraftTerm]:
    """Each term with the definitions of the defined words its scope uses added to its scope."""
    unique: dict[str, Definition] = {}
    for definition in definitions:
        unique.setdefault(definition.term.casefold(), definition)
    expanded = []
    for term in terms:
        used = [definition for definition in unique.values()
                if _mentions(term.scope, definition.term)]
        if used:
            meanings = " ".join(f'In this agreement, "{definition.term}" means {definition.meaning}.'
                                for definition in used)
            term = replace(term, scope=f"{term.scope.rstrip('. ')}. {meanings}")
        expanded.append(term)
    return expanded


def _mentions(text: str, word: str) -> bool:
    return re.search(rf"(?<!\w){re.escape(word)}(?!\w)", text, re.IGNORECASE) is not None
