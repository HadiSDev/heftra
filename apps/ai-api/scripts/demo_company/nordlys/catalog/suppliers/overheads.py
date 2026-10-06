"""Suppliers that run the company: software, telecom, premises, advisers, fleet, safety, travel."""
from __future__ import annotations

from datetime import date

from ..pricing import fixed, rising, stepped
from ..products import consumables as c
from ..products import office_services as o
from ..shapes import Billing
from .builders import offer, supplier

CLOUDDRIFT = supplier(
    "clouddrift", "CloudDrift ApS", "Copenhagen", "2210", "CD",
    "Managed IT provider for small and mid-sized companies: hosting, software subscriptions, "
    "backup and helpdesk.",
    (
        offer(o.PROJECT_PLATFORM, rising("1350.00", "0.05")),
        offer(o.ERP_HOSTING, rising("890.00")),
        offer(o.IT_SUPPORT, rising("2400.00")),
    ),
    seasonal=False, billing=Billing.MONTHLY)

SIGNALHUSET = supplier(
    "signalhuset-mobil", "Signalhuset Mobil ApS", "Odense", "2210", "SM",
    "Business mobile operator reseller with voice, data and 4G routers for companies.",
    (
        offer(o.MOBILE_SUBSCRIPTIONS, rising("1140.00")),
        offer(o.SITE_ROUTERS, fixed("1440.00")),
    ),
    seasonal=False, billing=Billing.MONTHLY)

KONTORHUSET = supplier(
    "kontorhuset", "Kontorhuset Danmark ApS", "Roskilde", "2220", "KH",
    "Office supplies dealer delivering paper, toner, stationery and kitchen supplies to "
    "businesses.",
    (
        offer(c.TONER, rising("96.00"), "2", "10", weight=1.5),
        offer(c.PAPER_A4, rising("24.80"), "4", "20", weight=1.5),
        offer(o.OFFICE_SUPPLIES, fixed("180.00"), jitter=0.5),
    ),
    per_month=1.5, lines=(1, 3), seasonal=False)

PAPIRGROSSISTEN = supplier(
    "papirgrossisten", "Papirgrossisten ApS", "Vejle", "2220", "PG",
    "Online wholesaler of paper, toner and office consumables at trade prices.",
    (
        offer(c.TONER, rising("78.00"), "2", "6"),
    ),
    per_month=0.5, lines=(1, 1), seasonal=False, first_day=date(2025, 5, 1))

VESTERGAARD_EJENDOMME = supplier(
    "vestergaard-erhverv", "Vestergaard Erhvervsejendomme A/S", "Køge", "2220", "VE",
    "Commercial property company letting offices, workshops and yards in the Køge area.",
    (
        offer(o.RENT, rising("7800.00", "0.025")),
        offer(o.UTILITIES, fixed("1150.00"), jitter=0.2),
    ),
    seasonal=False, billing=Billing.MONTHLY)

RENHOLD_SERVICE = supplier(
    "renhold-service", "Renhold Service ApS", "Køge", "2220", "RS",
    "Cleaning company for offices, canteens and site welfare cabins.",
    (
        offer(o.OFFICE_CLEANING, rising("1650.00")),
        offer(o.CABIN_CLEANING, rising("85.00"), "4", "12"),
    ),
    seasonal=False, billing=Billing.MONTHLY)

LIND_BECH = supplier(
    "lind-bech", "Advokatfirmaet Lind & Bech", "Copenhagen", "2230", "LB",
    "Law firm advising contractors and developers on construction contracts and disputes.",
    (
        offer(o.LEGAL_ADVICE, rising("285.00"), "4", "30", step="0.5"),
    ),
    per_month=0.4, lines=(1, 1), seasonal=False)

KJAER_PARTNERE = supplier(
    "kjaer-partnere", "Revisionsfirmaet Kjær & Partnere", "Roskilde", "2230", "KP",
    "Accounting firm providing bookkeeping, payroll and statutory audit for SMEs.",
    (
        offer(o.BOOKKEEPING, rising("2100.00")),
    ),
    seasonal=False, billing=Billing.MONTHLY)

KONSTRUKTOER_RAADGIVNING = supplier(
    "konstruktoer-raadgivning", "Konstruktør Rådgivning ApS", "Roskilde", "2230", "KR",
    "Consulting engineers for structural design, calculations and site supervision.",
    (
        offer(o.STRUCTURAL_ENGINEERING, rising("135.00"), "20", "90", step="0.5"),
    ),
    per_month=1.2, lines=(1, 1))

FLAADELEASING = supplier(
    "flaadeleasing-nord", "FlådeLeasing Nord A/S", "Aarhus", "2240", "FL",
    "Fleet leasing company for vans and company cars with service agreements.",
    (
        offer(o.VAN_LEASING, stepped("6480.00", (date(2026, 1, 1), "6720.00"))),
    ),
    seasonal=False, billing=Billing.MONTHLY)

AUTOVAERKSTED_SYD = supplier(
    "autovaerksted-syd", "Autoværksted Syd ApS", "Køge", "2240", "AS",
    "Independent workshop servicing vans and light trucks, with tyre hotel.",
    (
        offer(o.VEHICLE_SERVICE, fixed("640.00"), jitter=0.6, weight=2.0),
        offer(c.VAN_TYRES, rising("520.00"), "1", "2", weight=0.6),
    ),
    per_month=1.0, lines=(1, 2), seasonal=False)

SIKKERHEDSUDSTYR = supplier(
    "sikkerhedsudstyr", "Sikkerhedsudstyr ApS", "Brøndby", "2250", "SU",
    "Distributor of personal protective equipment for construction and industry.",
    (
        offer(c.GLOVES, rising("33.40"), "6", "40", weight=2.0),
        offer(c.HELMET, rising("18.90"), "5", "25"),
        offer(c.HIVIS_JACKET, rising("38.00"), "5", "20"),
        offer(c.SAFETY_BOOTS, rising("92.00"), "3", "12"),
    ),
    per_month=2.0, lines=(1, 3))

ARBEJDSTOEJ_NORD = supplier(
    "arbejdstoej-nord", "Arbejdstøj Nord ApS", "Aalborg", "2250", "AN",
    "Workwear supplier with logo printing for trades and contractors.",
    (
        offer(c.WORK_TROUSERS, rising("64.00"), "10", "40"),
        offer(c.SOFTSHELL, rising("79.00"), "10", "30"),
    ),
    per_month=0.7, lines=(1, 2), seasonal=False)

HOTEL_FJORDKANTEN = supplier(
    "hotel-fjordkanten", "Hotel Fjordkanten", "Svendborg", "2260", "HF",
    "Business hotel offering long-stay rates for site crews.",
    (
        offer(o.HOTEL_NIGHT, rising("118.00"), "6", "40"),
    ),
    per_month=1.0, lines=(1, 1))

REJSEBUREAU_NORD = supplier(
    "rejsebureau-nord", "Rejsebureau Nord ApS", "Copenhagen", "2260", "RN",
    "Business travel agency booking flights, rail and hotels.",
    (
        offer(o.FLIGHT_CPH_AAL, rising("210.00"), "1", "4"),
        offer(o.TRAIN_TICKETS, fixed("140.00"), jitter=0.5),
    ),
    per_month=0.6, lines=(1, 2), seasonal=False)

SUPPLIERS = (CLOUDDRIFT, SIGNALHUSET, KONTORHUSET, PAPIRGROSSISTEN, VESTERGAARD_EJENDOMME,
             RENHOLD_SERVICE, LIND_BECH, KJAER_PARTNERE, KONSTRUKTOER_RAADGIVNING, FLAADELEASING,
             AUTOVAERKSTED_SYD, SIKKERHEDSUDSTYR, ARBEJDSTOEJ_NORD, HOTEL_FJORDKANTEN,
             REJSEBUREAU_NORD)
