"""Suppliers of building materials, including the cheaper ones the alternatives point to."""
from __future__ import annotations

from datetime import date

from ..pricing import rising, stepped
from ..products import consumables as c
from ..products import materials as m
from ..products import site_services as s
from .builders import offer, supplier

CONCRETE_AGREEMENT_START = date(2026, 2, 1)
REBAR_AGREEMENT_START = date(2025, 10, 1)

NORDISK_BETON = supplier(
    "nordisk-beton", "Nordisk Beton ApS", "Køge", "2010", "NB",
    "Ready-mix concrete producer with three plants on Zealand, supplying housing and civil "
    "works projects with standard and special concretes, pumping and delivery planning.",
    (
        offer(m.CONCRETE_C3037,
              stepped("128.00", (CONCRETE_AGREEMENT_START, "126.00"), (date(2026, 6, 1), "132.00")),
              "18", "85", step="0.5", weight=3.0),
        offer(m.CONCRETE_C2530, rising("118.00"), "8", "40", step="0.5", weight=1.5),
        offer(s.CONCRETE_PUMPING, rising("165.00"), "3", "9", step="0.5", weight=1.4,
              discount="8", discount_since=CONCRETE_AGREEMENT_START, discount_share=0.45),
    ),
    per_month=9.0, lines=(1, 3))

BETONVAERKET_FYN = supplier(
    "betonvaerket-fyn", "Betonværket Fyn A/S", "Odense", "2010", "BF",
    "Independent concrete plant on Funen delivering ready-mix concrete to contractors in "
    "Funen and western Zealand.",
    (
        offer(m.CONCRETE_C3037, stepped("118.50", (date(2026, 1, 1), "121.00")), "10", "45",
              step="0.5", weight=2.0),
        offer(m.CONCRETE_C2530, stepped("110.00", (date(2026, 1, 1), "112.80")), "6", "30",
              step="0.5", weight=1.0),
    ),
    per_month=1.3, lines=(1, 2), first_day=date(2025, 3, 1))

JERNLAGER_DANMARK = supplier(
    "jernlager-danmark", "Jernlager Danmark A/S", "Vejle", "2010", "JD",
    "Steel stockholder and rebar processor with cut-and-bend service, supplying reinforcing "
    "steel, mesh and structural sections to the Danish construction industry.",
    (
        offer(m.REBAR_12,
              stepped("1020.00", (REBAR_AGREEMENT_START, "1010.00"), (date(2026, 5, 1), "1045.00")),
              "2", "12", step="0.25", weight=3.0),
        offer(m.REBAR_10, rising("1035.00"), "1", "5", step="0.25", weight=1.5),
        offer(m.MESH_K131, rising("24.50"), "40", "200", step="10", weight=1.5,
              discount="5", discount_since=REBAR_AGREEMENT_START, discount_share=0.6),
        offer(m.BEAM_HEB200, rising("98.00"), "12", "60", weight=0.8),
    ),
    per_month=4.5, lines=(1, 4))

BYGGELAGER_SYD = supplier(
    "byggelager-syd", "Byggelager Syd ApS", "Haderslev", "2010", "BS",
    "Builders' merchant for professionals in Southern Denmark with a broad range of timber, "
    "boards, insulation, steel, fixings and site consumables at trade prices.",
    (
        offer(m.REBAR_12, rising("975.00", "0.015"), "1", "4", step="0.25", weight=1.0),
        offer(m.OSB_18, rising("18.10"), "20", "80", step="5", weight=1.5),
        offer(c.GLOVES, rising("27.50"), "4", "16", weight=1.0),
        offer(m.WOOL_195, rising("6.85"), "60", "240", step="10", weight=1.0),
        offer(m.SCREWS_5X80, rising("14.20"), "5", "30", weight=1.2),
        offer(m.GYPSUM_13, rising("6.40"), "40", "200", step="10", weight=1.2),
    ),
    per_month=3.5, lines=(2, 5))

SKOV_TOMMER = supplier(
    "skov-tommer", "Skov & Tømmer A/S", "Silkeborg", "2010", "ST",
    "Timber merchant and planing mill supplying certified construction timber, boards and "
    "formwork materials to contractors across Jutland and Zealand.",
    (
        offer(m.TIMBER_45X195, rising("4.75"), "120", "900", step="10", weight=2.0),
        offer(m.TIMBER_45X95, rising("2.30"), "200", "1200", step="20", weight=1.5),
        offer(m.OSB_18, rising("20.60"), "40", "260", step="10", weight=2.0),
        offer(m.PLYWOOD_21, rising("46.50"), "10", "60", step="5", weight=1.0),
    ),
    per_month=5.5, lines=(2, 4))

TRAELAST_MIDT = supplier(
    "traelast-midt", "Trælast Midt ApS", "Herning", "2010", "TM",
    "Regional timber yard selling construction timber and boards to builders in Central "
    "Jutland.",
    (
        offer(m.TIMBER_45X195, rising("4.32"), "100", "500", step="10", weight=2.0),
        offer(m.TIMBER_45X95, rising("2.12"), "100", "600", step="20", weight=1.0),
    ),
    per_month=1.2, lines=(1, 2), first_day=date(2025, 2, 1))

ISOLERING_NORD = supplier(
    "isolering-nord", "Isolering Nord A/S", "Aalborg", "2010", "IN",
    "Insulation wholesaler stocking mineral wool, EPS and technical insulation, with direct "
    "site delivery across Denmark.",
    (
        offer(m.WOOL_195, rising("7.70"), "150", "900", step="10", weight=2.0),
        offer(m.WOOL_95, rising("4.10"), "100", "600", step="10", weight=1.2),
        offer(m.EPS_100, rising("6.20"), "80", "400", step="10", weight=1.0),
    ),
    per_month=2.8, lines=(1, 3))

VVS_GROSSISTEN = supplier(
    "vvs-grossisten-oest", "VVS-Grossisten Øst ApS", "Roskilde", "2010", "VG",
    "Plumbing and heating wholesaler serving installers and contractors on Zealand with pipes, "
    "fittings, valves and drainage.",
    (
        offer(m.COPPER_15, rising("7.90"), "50", "400", step="5", weight=1.5),
        offer(m.PEX_16, rising("1.85"), "100", "600", step="50", weight=1.2),
        offer(m.DRAIN_110, rising("14.80"), "6", "40", weight=1.0),
        offer(m.VALVE_DN15, rising("9.40"), "6", "40", weight=1.0),
    ),
    per_month=3.0, lines=(2, 4))

EL_LAGER = supplier(
    "el-lager-nord", "El-Lager Nord ApS", "Aarhus", "2010", "EL",
    "Electrical wholesaler supplying installation cable, wiring devices and lighting to "
    "electricians and contractors.",
    (
        offer(m.CABLE_3G15, rising("0.96"), "300", "2000", step="100", weight=2.0),
        offer(m.CABLE_5G25, rising("2.35"), "100", "600", step="50", weight=1.0),
        offer(m.SOCKET_DOUBLE, rising("11.90"), "10", "80", weight=1.0),
        offer(m.LED_PANEL, rising("34.50"), "6", "40", weight=1.0),
    ),
    per_month=2.5, lines=(2, 4))

SUPPLIERS = (NORDISK_BETON, BETONVAERKET_FYN, JERNLAGER_DANMARK, BYGGELAGER_SYD, SKOV_TOMMER,
             TRAELAST_MIDT, ISOLERING_NORD, VVS_GROSSISTEN, EL_LAGER)
