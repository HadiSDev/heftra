"""Goods used up rather than built in: fuel, protective equipment, workwear, office supplies."""
from __future__ import annotations

from ..shapes import ProductSpec
from ..specs import described, goods, numeric

DIESEL = ProductSpec(
    "diesel", "Diesel, road grade", "Diesel EN 590, delivered to site tank", "l", "4410", "324110",
    goods("diesel fuel", "Diesel, road grade", "l", described("standard", "EN 590")))
ADBLUE = ProductSpec(
    "adblue", "AdBlue", "AdBlue (AUS 32) delivered in 1,000 l IBC", "l", "4410", "325180",
    goods("diesel exhaust fluid", "AdBlue", "l", described("standard", "ISO 22241")))
GLOVES = ProductSpec(
    "gloves-nitrile", "Nitrile-coated work gloves",
    "Nitrile-coated knitted gloves, size 9–10, EN 388 4131X, pack of 12 pairs", "pk", "6510",
    "339113",
    goods("work gloves", "Nitrile-coated work gloves", "pack",
          described("standard", "EN 388 4131X"), described("size", "9–10"),
          numeric("pairs_per_pack", "12 pairs", 12, "pairs", "more"),
          item_class="finished_good"))
HELMET = ProductSpec(
    "helmet", "Safety helmet EN 397, white", "Safety helmet with 6-point harness and chin strap",
    "stk", "6510", "339113",
    goods("safety helmet", "Safety helmet EN 397, white", "piece",
          described("standard", "EN 397"), item_class="finished_good"))
HIVIS_JACKET = ProductSpec(
    "hivis-jacket", "Hi-vis jacket class 3",
    "High-visibility jacket EN ISO 20471 class 3, yellow, reflective tape", "stk", "6510", "315000",
    goods("high-visibility jacket", "Hi-vis jacket class 3", "piece",
          described("standard", "EN ISO 20471 class 3"), described("colour", "yellow"),
          item_class="finished_good"))
SAFETY_BOOTS = ProductSpec(
    "safety-boots", "Safety boots S3", "Safety boots S3 SRC, composite toe cap", "par", "6510",
    "316000",
    goods("safety boots", "Safety boots S3", "piece", described("standard", "EN ISO 20345 S3"),
          item_class="finished_good", units_per_line_unit=1))
WORK_TROUSERS = ProductSpec(
    "work-trousers", "Work trousers with knee pockets",
    "Stretch work trousers, holster pockets, Cordura knee pockets", "stk", "6520", "315000",
    goods("work trousers", "Work trousers with knee pockets", "piece",
          item_class="finished_good"))
SOFTSHELL = ProductSpec(
    "softshell", "Softshell jacket with logo print", "Softshell jacket, company logo on chest",
    "stk", "6520", "315000",
    goods("softshell jacket", "Softshell jacket with logo print", "piece",
          item_class="finished_good"))
TONER = ProductSpec(
    "toner-black", "Black toner cartridge, 3,000 pages",
    "Black toner for the office laser printers, 3,000-page yield", "stk", "6210", "339940",
    goods("toner cartridge", "Black toner cartridge, 3,000 pages", "piece",
          described("colour", "black"), numeric("page_yield", "3,000 pages", 3000, "pages"),
          item_class="finished_good"))
PAPER_A4 = ProductSpec(
    "paper-a4", "Copy paper A4 80 g", "A4 80 g/m² copy paper, box of 5 × 500 sheets", "pk", "6210",
    "322120",
    goods("copy paper", "Copy paper A4 80 g", "pack", described("format", "A4"),
          numeric("weight", "80 g/m²", 80, "g/m2", "equal"),
          numeric("sheets", "2,500 sheets", 2500, "sheets")))
VAN_TYRES = ProductSpec(
    "tyres-van", "Van tyres 215/65 R16C, set of 4", "All-season van tyres incl. fitting",
    "set", "6420", "326210",
    goods("van tyres", "Van tyres 215/65 R16C", "piece", described("size", "215/65 R16C"),
          item_class="part", units_per_line_unit=4))
