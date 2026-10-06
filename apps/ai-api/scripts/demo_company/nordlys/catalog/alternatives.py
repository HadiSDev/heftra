"""The cheaper alternatives the demo company's last scan found. History alternatives are the same
product bought cheaper from another of its suppliers; benchmark and marketplace ones are priced
against the item's own unit price."""
from __future__ import annotations

from .shapes import AlternativeSpec

HISTORY = "history"
BENCHMARK = "benchmark"
MARKETPLACE = "marketplace"
EXACT = "exact"
EQUIVALENT = "equivalent"


def _history(supplier: str, product: str, cheaper: str, days_ago: int = 3) -> AlternativeSpec:
    return AlternativeSpec(supplier=supplier, product=product, source=HISTORY, match=EXACT,
                           cheaper_supplier=cheaper, found_days_ago=days_ago)


def _benchmark(supplier: str, product: str, ratio: str, organizations: int,
               days_ago: int = 3) -> AlternativeSpec:
    return AlternativeSpec(supplier=supplier, product=product, source=BENCHMARK,
                           match=EQUIVALENT, price_ratio=ratio,
                           origin={"by": "specification", "organizations": organizations},
                           found_days_ago=days_ago)


ALTERNATIVES: tuple[AlternativeSpec, ...] = (
    _history("nordisk-beton", "concrete-c3037", "betonvaerket-fyn", 2),
    _history("jernlager-danmark", "rebar-12", "byggelager-syd", 2),
    _history("skov-tommer", "osb-18", "byggelager-syd", 4),
    _history("skov-tommer", "timber-45x195", "traelast-midt", 4),
    _history("isolering-nord", "wool-195", "byggelager-syd", 5),
    _history("braendstof-nord", "diesel", "tankpartner-oest", 1),
    _history("sikkerhedsudstyr", "gloves-nitrile", "byggelager-syd", 6),
    _history("kontorhuset", "toner-black", "papirgrossisten", 6),
    _benchmark("nordisk-beton", "concrete-c2530", "0.935", 11, 2),
    _benchmark("jernlager-danmark", "rebar-12", "0.958", 14, 2),
    _benchmark("vvs-grossisten-oest", "copper-15", "0.905", 9, 5),
    _benchmark("el-lager-nord", "cable-3g15", "0.878", 12, 5),
    _benchmark("skov-tommer", "plywood-21", "0.893", 8, 4),
    AlternativeSpec(
        supplier="sikkerhedsudstyr", product="hivis-jacket", source=MARKETPLACE,
        match=EQUIVALENT, price_ratio="0.79", name="Hi-vis softshell jacket class 3, yellow",
        origin={"connector": "web", "seller": "Arbejdssikker Webshop",
                "url": "https://arbejdssikker-webshop.example/hi-vis/softshell-class-3",
                "availability": "In stock", "shipping": "Free delivery over EUR 100"},
        verdicts={"standard": ("same", "EN ISO 20471 class 3", "Same certification."),
                  "colour": ("same", "yellow", "")},
        found_days_ago=6),
    AlternativeSpec(
        supplier="el-lager-nord", product="led-panel", source=MARKETPLACE, match=EQUIVALENT,
        price_ratio="0.81", name="LED panel 600 × 600, 34 W, 4000 K, 3,700 lm",
        origin={"connector": "web", "seller": "LysGrossisten Online",
                "url": "https://lysgrossisten-online.example/led-panel-600-34w",
                "availability": "In stock, 2–3 days", "shipping": "EUR 9.50 per order"},
        verdicts={"power": ("better", "34 W", "Uses 2 W less."),
                  "luminous_flux": ("better", "3,700 lm", "100 lm brighter."),
                  "colour_temperature": ("same", "4000 K", "")},
        found_days_ago=5),
)
