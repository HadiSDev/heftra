"""Danish-looking VAT numbers that no real company can have."""
from __future__ import annotations

import hashlib

CVR_WEIGHTS = (2, 7, 6, 5, 4, 3, 2, 1)


def fictional_vat(key: str) -> str:
    """`DK` and eight digits derived from `key`, changed until they fail the CVR checksum that
    every real Danish CVR number passes."""
    digits = [int(char) for char in str(int(hashlib.sha256(key.encode()).hexdigest(), 16))[:8]]
    if digits[0] == 0:
        digits[0] = 3
    while _passes_checksum(digits):
        digits[-1] = (digits[-1] + 1) % 10
    return "DK" + "".join(str(digit) for digit in digits)


def _passes_checksum(digits: list[int]) -> bool:
    return sum(weight * digit for weight, digit in zip(CVR_WEIGHTS, digits)) % 11 == 0
