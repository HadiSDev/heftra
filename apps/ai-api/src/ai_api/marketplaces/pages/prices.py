"""Prices as pages and APIs write them: 1249.00, 1.249,00 kr., "DKK 1 249,-"."""
from __future__ import annotations

import re
from decimal import Decimal, InvalidOperation

_NOT_NUMBER = re.compile(r"[^\d.,]")


def parse_price(value: object) -> Decimal | None:
    """The amount in a price, reading the last separator followed by one or two digits as the
    decimal point; None when there is no amount."""
    if isinstance(value, (int, float, Decimal)):
        return Decimal(str(value))
    if not isinstance(value, str):
        return None
    text = _NOT_NUMBER.sub("", value.replace(",-", "")).strip(".,")
    if not text or not any(character.isdigit() for character in text):
        return None
    decimal_at = max(text.rfind(","), text.rfind("."))
    if decimal_at != -1 and 1 <= len(text) - decimal_at - 1 <= 2:
        whole = re.sub(r"[.,]", "", text[:decimal_at])
        number = f"{whole or '0'}.{text[decimal_at + 1:]}"
    else:
        number = re.sub(r"[.,]", "", text)
    try:
        return Decimal(number)
    except InvalidOperation:
        return None
