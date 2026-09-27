"""What the model is told when it reads an agreement."""
from __future__ import annotations

HEADER = (
    "You are reading the first pages of a trade or framework agreement between a customer "
    "and a supplier. Report who the supplier is (name, VAT or CVR number with its country, "
    "website), the customer's name, the agreement's title and reference, when it starts and "
    "ends (dates as YYYY-MM-DD), the currency its prices are in (ISO code), and a one-sentence "
    "summary. Leave anything the pages do not state as null. Do not guess."
)

TERMS = (
    "You are reading pages of a trade or framework agreement between a customer and a "
    "supplier. List every term that says what the customer must buy from this supplier, what "
    "the supplier charges, or what the customer commits to. Use one of these kinds:\n"
    "- preferred_supplier: goods or services the customer shall buy from this supplier. Put "
    "what is covered in scope, and any condition (for example \"when in stock\") in "
    "conditions.\n"
    "- agreed_price: one item at an agreed unit price. Put the exact item (make, model, "
    "product number) in item, the price in unit_price, what the price is per in unit, and the "
    "currency.\n"
    "- discount: a percentage off a range of goods or services. Put the range in scope and "
    "the percentage in discount_percent.\n"
    "- volume_commitment: an amount the customer commits to spend. Put it in "
    "commitment_amount, the period (month, quarter, year or agreement) in commitment_period, "
    "and any rebate tiers as thresholds with rebate percentages.\n"
    "For every term, copy the sentence it comes from word for word into quote, and give the "
    "page number printed in the \"--- Page N ---\" marker it appears under. Give a confidence "
    "from 0 to 1. Leave out general legal clauses (liability, termination, confidentiality). "
    "If these pages hold no such terms, return an empty list. Do not invent terms or quotes."
)


def page_marker(number: int) -> str:
    return f"--- Page {number} ---"
