"""Building materials: concrete, steel, timber, insulation, installation supplies and boards."""
from __future__ import annotations

from ..shapes import ProductSpec
from ..specs import described, goods, numeric

CONCRETE_C3037 = ProductSpec(
    "concrete-c3037", "Ready-mix concrete C30/37",
    "Ready-mix concrete C30/37, exposure class XC3, Dmax 16 mm, slump S3", "m3", "4110", "327320",
    goods("ready-mix concrete", "Ready-mix concrete C30/37", "m3",
          described("strength_class", "C30/37"), described("exposure_class", "XC3"),
          numeric("max_aggregate_size", "16 mm", 16, "mm", "equal")))
CONCRETE_C2530 = ProductSpec(
    "concrete-c2530", "Ready-mix concrete C25/30",
    "Ready-mix concrete C25/30, exposure class XC1, Dmax 16 mm, slump S3", "m3", "4110", "327320",
    goods("ready-mix concrete", "Ready-mix concrete C25/30", "m3",
          described("strength_class", "C25/30"), described("exposure_class", "XC1"),
          numeric("max_aggregate_size", "16 mm", 16, "mm", "equal")))
REBAR_12 = ProductSpec(
    "rebar-12", "Rebar B500B Ø12 mm", "Reinforcing steel B500B, Ø12 mm, 12 m lengths", "t",
    "4130", "331110",
    goods("reinforcing steel bar", "Rebar B500B Ø12 mm", "kg", described("grade", "B500B"),
          numeric("diameter", "12 mm", 12, "mm", "equal"),
          numeric("length", "12 m", 12, "m", "equal")))
REBAR_10 = ProductSpec(
    "rebar-10", "Rebar B500B Ø10 mm", "Reinforcing steel B500B, Ø10 mm, 12 m lengths", "t",
    "4130", "331110",
    goods("reinforcing steel bar", "Rebar B500B Ø10 mm", "kg", described("grade", "B500B"),
          numeric("diameter", "10 mm", 10, "mm", "equal"),
          numeric("length", "12 m", 12, "m", "equal")))
MESH_K131 = ProductSpec(
    "mesh-k131", "Reinforcement mesh K131", "Welded mesh Ø5 mm / 150 mm, 2.35 × 5.00 m sheet",
    "stk", "4130", "331200",
    goods("welded reinforcement mesh", "Reinforcement mesh K131", "sheet",
          numeric("wire_diameter", "5 mm", 5, "mm", "equal"),
          numeric("mesh_spacing", "150 mm", 150, "mm", "equal"),
          described("sheet_size", "2.35 × 5.00 m"), units_per_line_unit=1))
BEAM_HEB200 = ProductSpec(
    "beam-heb200", "Steel beam HE200B S355", "Hot-rolled H-beam HE200B, S355JR, cut to length",
    "m", "4130", "332310",
    goods("structural steel beam", "Steel beam HE200B S355", "m",
          described("profile", "HE200B"), described("steel_grade", "S355JR")))
TIMBER_45X195 = ProductSpec(
    "timber-45x195", "Construction timber C24 45 × 195 mm",
    "Planed kiln-dried spruce, strength class C24, PEFC certified", "m", "4120", "321100",
    goods("structural timber", "Construction timber C24 45 × 195 mm", "m",
          described("strength_class", "C24"), described("cross_section", "45 × 195 mm"),
          described("certification", "PEFC")))
TIMBER_45X95 = ProductSpec(
    "timber-45x95", "Construction timber C24 45 × 95 mm",
    "Planed kiln-dried spruce, strength class C24, PEFC certified", "m", "4120", "321100",
    goods("structural timber", "Construction timber C24 45 × 95 mm", "m",
          described("strength_class", "C24"), described("cross_section", "45 × 95 mm"),
          described("certification", "PEFC")))
OSB_18 = ProductSpec(
    "osb-18", "OSB/3 board 18 mm", "OSB/3 board, 18 mm, 1220 × 2440 mm, tongue and groove", "stk",
    "4120", "321200",
    goods("oriented strand board", "OSB/3 board 18 mm", "sheet", described("grade", "OSB/3"),
          numeric("thickness", "18 mm", 18, "mm", "equal"),
          described("format", "1220 × 2440 mm"), units_per_line_unit=1))
PLYWOOD_21 = ProductSpec(
    "plywood-21", "Formwork plywood 21 mm", "Film-faced birch plywood, 21 mm, 1250 × 2500 mm",
    "stk", "4120", "321200",
    goods("formwork plywood", "Formwork plywood 21 mm", "sheet",
          numeric("thickness", "21 mm", 21, "mm", "equal"),
          described("format", "1250 × 2500 mm"), described("face", "film-faced birch"),
          units_per_line_unit=1))
WOOL_195 = ProductSpec(
    "wool-195", "Mineral wool batts 195 mm",
    "Mineral wool batts λ37, 195 mm, 565 × 1200 mm, sold per m²", "m2", "4140", "327993",
    goods("mineral wool insulation", "Mineral wool batts 195 mm", "m2",
          numeric("thickness", "195 mm", 195, "mm", "equal"),
          numeric("thermal_conductivity", "0.037 W/mK", 0.037, "W/mK", "less")))
WOOL_95 = ProductSpec(
    "wool-95", "Mineral wool batts 95 mm",
    "Mineral wool batts λ37, 95 mm, 565 × 1200 mm, sold per m²", "m2", "4140", "327993",
    goods("mineral wool insulation", "Mineral wool batts 95 mm", "m2",
          numeric("thickness", "95 mm", 95, "mm", "equal"),
          numeric("thermal_conductivity", "0.037 W/mK", 0.037, "W/mK", "less")))
EPS_100 = ProductSpec(
    "eps-100", "EPS 80 floor insulation 100 mm",
    "Expanded polystyrene EPS 80, 100 mm, 1200 × 600 mm boards", "m2", "4140", "326190",
    goods("EPS insulation board", "EPS 80 floor insulation 100 mm", "m2",
          described("grade", "EPS 80"), numeric("thickness", "100 mm", 100, "mm", "equal")))
COPPER_15 = ProductSpec(
    "copper-15", "Copper pipe 15 × 1.0 mm", "Hard-drawn copper water pipe, EN 1057, 5 m lengths",
    "m", "4150", "331420",
    goods("copper pipe", "Copper pipe 15 × 1.0 mm", "m",
          numeric("outer_diameter", "15 mm", 15, "mm", "equal"),
          numeric("wall_thickness", "1.0 mm", 1.0, "mm", "more"),
          described("standard", "EN 1057")))
PEX_16 = ProductSpec(
    "pex-16", "PEX-AL-PEX pipe 16 mm", "Multilayer pipe 16 × 2.0 mm, 100 m coil", "m", "4150",
    "326120",
    goods("multilayer pipe", "PEX-AL-PEX pipe 16 mm", "m",
          numeric("outer_diameter", "16 mm", 16, "mm", "equal")))
DRAIN_110 = ProductSpec(
    "drain-110", "PP drain pipe 110 mm × 3 m", "Polypropylene soil and waste pipe with socket",
    "stk", "4150", "326120",
    goods("drain pipe", "PP drain pipe 110 mm × 3 m", "piece",
          numeric("diameter", "110 mm", 110, "mm", "equal"), item_class="part"))
VALVE_DN15 = ProductSpec(
    "valve-dn15", "Ball valve DN15, brass", "Full-bore ball valve DN15, PN25, lever handle", "stk",
    "4150", "33291A",
    goods("ball valve", "Ball valve DN15, brass", "piece", described("size", "DN15"),
          described("pressure_rating", "PN25"), item_class="part"))
CABLE_3G15 = ProductSpec(
    "cable-3g15", "Installation cable PVIK 3G1.5 mm²",
    "PVC-insulated installation cable 300/500 V, 100 m drum", "m", "4150", "335930",
    goods("installation cable", "Installation cable PVIK 3G1.5 mm²", "m",
          described("cable_type", "PVIK"), described("conductors", "3G1.5 mm²"),
          described("voltage", "300/500 V")))
CABLE_5G25 = ProductSpec(
    "cable-5g25", "Installation cable PVIK 5G2.5 mm²",
    "PVC-insulated installation cable 300/500 V, 100 m drum", "m", "4150", "335930",
    goods("installation cable", "Installation cable PVIK 5G2.5 mm²", "m",
          described("cable_type", "PVIK"), described("conductors", "5G2.5 mm²"),
          described("voltage", "300/500 V")))
SOCKET_DOUBLE = ProductSpec(
    "socket-double", "Double socket outlet, flush-mounted", "2-gang earthed socket outlet, white",
    "stk", "4150", "335930",
    goods("socket outlet", "Double socket outlet, flush-mounted", "piece",
          described("gangs", "2"), item_class="part"))
LED_PANEL = ProductSpec(
    "led-panel", "LED panel 600 × 600, 36 W", "Recessed LED panel, 4000 K, 3,600 lm, UGR<19",
    "stk", "4150", "335110",
    goods("LED panel", "LED panel 600 × 600, 36 W", "piece",
          numeric("power", "36 W", 36, "W", "less"),
          numeric("luminous_flux", "3,600 lm", 3600, "lm", "more"),
          numeric("colour_temperature", "4000 K", 4000, "K", "equal"),
          item_class="finished_good"))
GYPSUM_13 = ProductSpec(
    "gypsum-13", "Gypsum board 13 mm", "Standard gypsum board, 13 mm, 1200 × 2400 mm", "stk",
    "4160", "327400",
    goods("gypsum board", "Gypsum board 13 mm", "sheet",
          numeric("thickness", "13 mm", 13, "mm", "equal"),
          described("format", "1200 × 2400 mm"), units_per_line_unit=1))
SCREWS_5X80 = ProductSpec(
    "screws-5x80", "Construction screws 5 × 80 mm", "Torx wood screws, zinc-plated, box of 200",
    "pk", "4160", "332999",
    goods("wood screws", "Construction screws 5 × 80 mm", "pack",
          described("size", "5 × 80 mm"), numeric("count", "200 pcs", 200, "pcs", "more"),
          item_class="part"))
