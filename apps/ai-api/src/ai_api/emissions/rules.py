"""The rules both matchers follow, so the agent and its fallback judge a line alike."""
from __future__ import annotations

MATCHING_RULES = (
    "Apply these rules:\n"
    "- Classify by the product or service itself, not by the supplier's name or trade. Fragrance "
    "and perfume oils are chemical or cosmetic ingredients, not food flavourings; a laptop is a "
    "computer even when bought from a marketplace.\n"
    "- Taxes, duties, levies, public contributions and statutory fees (for example "
    "\"afgift\", \"bidrag\", \"garantifond\", VAT, customs) buy nothing: answer that no sector "
    "fits. Insurance premiums, bank fees and subscriptions are services and do get a sector.\n"
    "- Confidence: 0.9 only when the line plainly names what was bought and one sector clearly "
    "covers it; 0.5 to 0.7 when you inferred it from the supplier or the spend category; 0.3 "
    "or lower when you are choosing the closest of poor options."
)
