"""Subcontractors, machine hire, fuel, power, haulage and waste: what keeps the sites running."""
from __future__ import annotations

from datetime import date

from ..pricing import rising, stepped
from ..products import consumables as c
from ..products import site_services as s
from ..shapes import Billing
from .builders import offer, supplier

ELINSTALLATOR_HOLM = supplier(
    "elinstallator-holm", "Elinstallatør Holm ApS", "Ringsted", "2020", "EH",
    "Electrical contractor for housing and commercial new-build: installations, switchboards, "
    "lighting and data cabling.",
    (
        offer(s.ELECTRICIAN_HOURS, rising("62.00"), "120", "380", step="0.5", weight=2.0),
        offer(s.ELECTRICAL_MATERIALS, rising("4800.00"), jitter=0.5),
    ),
    per_month=2.0, lines=(1, 2))

VVS_HANSEN = supplier(
    "vvs-varme-hansen", "VVS & Varme Hansen A/S", "Næstved", "2020", "VH",
    "Plumbing and heating contractor installing water, drainage, heating and ventilation in "
    "new residential and public buildings.",
    (
        offer(s.PLUMBER_HOURS, rising("64.00"), "100", "300", step="0.5", weight=2.0),
        offer(s.HEATING_MATERIALS, rising("3900.00"), jitter=0.5),
    ),
    per_month=1.6, lines=(1, 2))

JORD_KLOAK_VEST = supplier(
    "jord-kloak-vest", "Jord & Kloak Vest A/S", "Slagelse", "2020", "JK",
    "Groundworks contractor for excavation, foundations, drainage and sewer connections on "
    "building and infrastructure projects.",
    (
        offer(s.GROUNDWORKS_STAGE, rising("21000.00"), jitter=0.45, weight=2.0),
        offer(s.SEWER_CONNECTION, rising("6500.00"), jitter=0.4),
    ),
    per_month=1.2, lines=(1, 2))

STILLADS_PARTNER = supplier(
    "stillads-partner", "Stillads Partner ApS", "Køge", "2020", "SP",
    "Scaffolding company providing facade and system scaffolding with erection, inspection and "
    "dismantling for contractors on Zealand.",
    (
        offer(s.SCAFFOLD_HIRE, rising("1450.00"), "2", "8", weight=2.0),
        offer(s.SCAFFOLD_ERECTION, rising("3800.00"), jitter=0.4),
    ),
    per_month=2.0, lines=(1, 2))

MASKINUDLEJNING_VEST = supplier(
    "maskinudlejning-vest", "MaskinUdlejning Vest A/S", "Holbæk", "2030", "MV",
    "Machine hire company renting excavators, loaders, telehandlers and site cabins to "
    "contractors, with delivery and service.",
    (
        offer(s.EXCAVATOR_5T, rising("245.00"), "3", "15", weight=2.0),
        offer(s.LOADER_8T, rising("395.00"), "2", "10", weight=1.0),
        offer(s.TELEHANDLER_14M, rising("310.00"), "2", "12", weight=1.2),
        offer(s.SITE_CABIN, rising("640.00"), "1", "3", weight=0.8),
    ),
    per_month=3.5, lines=(1, 3))

KRAN_LIFT_SERVICE = supplier(
    "kran-lift-service", "Kran & Lift Service ApS", "Greve", "2030", "KL",
    "Crane hire with operators and a fleet of scissor and boom lifts for building sites.",
    (
        offer(s.CRANE_60T, rising("185.00"), "4", "16", step="0.5", weight=1.5),
        offer(s.SCISSOR_LIFT, rising("115.00"), "2", "10"),
    ),
    per_month=1.3, lines=(1, 2))

BRAENDSTOF_NORD = supplier(
    "braendstof-nord", "Brændstof Nord A/S", "Kalundborg", "2040", "BN",
    "Fuel distributor delivering diesel, heating oil and AdBlue to site tanks and fleets "
    "across Zealand.",
    (
        offer(c.DIESEL,
              stepped("1.49", (date(2025, 7, 1), "1.46"), (date(2026, 1, 1), "1.53"),
                      (date(2026, 7, 1), "1.56")),
              "1500", "4500", step="50", weight=3.0),
        offer(c.ADBLUE, rising("0.62"), "200", "1000", step="50"),
    ),
    per_month=4.0, lines=(1, 2))

TANKPARTNER_OEST = supplier(
    "tankpartner-oest", "TankPartner Øst ApS", "Roskilde", "2040", "TP",
    "Independent fuel supplier delivering diesel to construction sites and farms on Zealand.",
    (
        offer(c.DIESEL, stepped("1.40", (date(2026, 1, 1), "1.44")), "800", "2400", step="50"),
    ),
    per_month=1.0, lines=(1, 1), first_day=date(2025, 4, 1))

BYGGESTROEM = supplier(
    "byggestroem-danmark", "Byggestrøm Danmark A/S", "Glostrup", "2040", "BD",
    "Supplier of temporary power to construction sites: connection, metering and supply.",
    (
        offer(s.SITE_POWER, rising("0.31"), "6000", "18000", step="100"),
    ),
    billing=Billing.MONTHLY)

FRAGTCENTRALEN = supplier(
    "fragtcentralen", "Fragtcentralen ApS", "Taastrup", "2050", "FC",
    "Haulage company with crane trucks and a pallet network delivering building materials to "
    "sites on Zealand.",
    (
        offer(s.HAULAGE, rising("92.00"), "4", "20", step="0.5", weight=2.0),
        offer(s.PALLET_DELIVERY, rising("68.00"), "2", "10"),
    ),
    per_month=3.5, lines=(1, 2))

AFFALDSLOESNINGER = supplier(
    "affaldsloesninger-oest", "Affaldsløsninger Øst ApS", "Køge", "2050", "AO",
    "Waste contractor providing skips, sorting and recycling of construction waste.",
    (
        offer(s.SKIP_HIRE, rising("285.00"), "2", "8", weight=2.0),
        offer(s.WASTE_HANDLING, rising("98.00"), "3", "20", step="0.5"),
    ),
    per_month=2.5, lines=(1, 2))

SUPPLIERS = (ELINSTALLATOR_HOLM, VVS_HANSEN, JORD_KLOAK_VEST, STILLADS_PARTNER,
             MASKINUDLEJNING_VEST, KRAN_LIFT_SERVICE, BRAENDSTOF_NORD, TANKPARTNER_OEST,
             BYGGESTROEM, FRAGTCENTRALEN, AFFALDSLOESNINGER)
