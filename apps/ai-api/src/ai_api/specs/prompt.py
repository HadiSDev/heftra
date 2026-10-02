"""What the specification reader is shown: one item, or a numbered batch of them."""
from __future__ import annotations

from dataclasses import dataclass

from web_api.specs.specification import Specification

from ..parsing import json_format_hint
from .reply import BatchSpecifications


@dataclass(frozen=True)
class ItemText:
    """What is known of an item when its specification is read."""

    item_name: str | None
    description: str | None
    unit: str | None
    category: str | None
    supplier: str | None


_RULES = [
    "You read what a company bought into a product specification, so cheaper products that are "
    "the same or as good can be found. Use only what the text says or what the product "
    "unmistakably is; never guess a part number, EAN or size.",
    "item_class: \"material\" when it is bought by weight, length, area or volume, or as stock "
    "to be cut, machined or processed (steel, wood, plastic granulate, cable by the metre); "
    "\"part\" when it is a component bought by the piece to be built into something or to "
    "maintain a machine, usually known by its maker's part number (bearings, screws, "
    "connectors, motors, valves, filters, cutting inserts, spare parts); \"finished_good\" "
    "when it is used as it is (laptops, toilet paper, snacks, phones, cleaning products); "
    "\"service\" when it is not a physical product: a service, fee, subscription, licence, "
    "insurance, travel, shipping, rent, utility or tax (with pricing_unit piece).",
    "product_type: a short English noun phrase saying what kind of product it is and for what "
    "use, e.g. \"business laptop\", \"hot-rolled round bar\", \"network installation cable\", "
    "\"toilet paper\".",
    "name: the product's short name as shops sell it, the product line first, e.g. \"MacBook "
    "Pro 14 M5 Pro\", \"ThinkPad T14 Gen 5\", \"Cat6 U/UTP installation cable\"; never only a "
    "component such as the processor. brand, model, part_number (the manufacturer's part "
    "number) and gtin (EAN) only when the text states them.",
    "attributes: the 2 to 6 attributes a buyer must not get less of, with snake_case English "
    "names. Each has a kind:",
    "- \"numeric\" with number (the number alone), unit and direction: \"more\" when more is better (memory, "
    "storage, sheets per roll, ply), \"less\" when less is better (weight of a laptop, power "
    "use), \"equal\" when it must match (a diameter, a cut length, a thread, a screen size, a "
    "voltage);",
    "- \"tiered\" for parts sold in ranked lines, with family, tier and generation: a processor "
    "(family \"Intel Core\", tier \"i7\", generation \"13\"; family \"Intel Core Ultra\", tier "
    "\"7\", generation \"1\"; family \"AMD Ryzen\", tier \"7\", generation \"7000\"; family "
    "\"Apple M\", tier \"Pro\", generation \"3\"), a graphics card, a steel or quality grade "
    "(family \"EN 10025\", tier \"S235\", generation null). A computer's processor is always "
    "a tiered attribute named \"processor\";",
    "- \"other\" for anything else (a material, a coating, a jacket, a certification), with "
    "its value.",
    "pricing_unit: the unit the product is naturally priced by, one of kg, m, m2, m3, l, "
    "piece, sheet, roll, pack. Materials by kg, m, m2, m3 or l; finished goods by piece, roll "
    "or sheet; pack only when the pack can't be counted in one of the others.",
    "units_per_line_unit: how many pricing units one unit of the line (\"Bought per\") holds, "
    "when the text says (a box of 305 m with pricing_unit m is 305; a pack of 8 rolls with "
    "pricing_unit roll is 8; a 10 g tube with pricing_unit kg is 0.01; a 250 ml bottle with "
    "pricing_unit l is 0.25); 1 when the line's unit is the pricing unit; null when unknown.",
    "confidence: from 0 to 1, how sure you are of the class, the pricing unit and the pack "
    "size.",
]


def spec_prompt(item: ItemText) -> str:
    return "\n".join([*_RULES, "", "Purchase:", *_lines(item), "",
                      json_format_hint(Specification)])


def batch_spec_prompt(items: list[ItemText]) -> str:
    purchases: list[str] = []
    for number, item in enumerate(items, start=1):
        purchases.extend([f"Purchase {number}:", *_lines(item), ""])
    return "\n".join([
        *_RULES, "",
        f"Read each of these {len(items)} purchases on its own, and answer for every one by "
        "its number.", "",
        *purchases,
        json_format_hint(BatchSpecifications),
    ])


def _lines(item: ItemText) -> list[str]:
    return [
        f"Item: {item.item_name or '(none)'}",
        f"Description: {item.description or '(none)'}",
        f"Bought per: {item.unit or '(none)'}",
        f"Spend category: {item.category or '(none)'}",
        f"Supplier: {item.supplier or '(unknown)'}",
    ]
