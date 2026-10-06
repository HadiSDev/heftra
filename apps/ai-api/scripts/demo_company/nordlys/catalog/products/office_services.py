"""Services that run the company: software, telecom, premises, advisers, fleet and travel."""
from __future__ import annotations

from .builders import service_product


PROJECT_PLATFORM = service_product(
    "project-platform", "Project management platform, 45 users",
    "Monthly subscription incl. document control and site diary", "months", "6110", "511200",
    "software subscription")
ERP_HOSTING = service_product(
    "erp-hosting", "ERP and payroll hosting", "Monthly hosting, backup and licences", "months",
    "6110", "511200", "software subscription")
IT_SUPPORT = service_product(
    "it-support", "IT support retainer", "Managed IT support and helpdesk, weekdays 8–17",
    "months", "6120", "541512", "IT support")
MOBILE_SUBSCRIPTIONS = service_product(
    "mobile-subscriptions", "Mobile subscriptions, 38 lines", "Voice and data, monthly",
    "months", "6130", "517210", "mobile subscription")
SITE_ROUTERS = service_product(
    "site-routers", "Site 4G routers", "4G routers and data for site cabins, monthly", "months",
    "6130", "517210", "mobile data")
OFFICE_SUPPLIES = service_product(
    "office-supplies", "Office supplies, assorted", "Pens, binders, labels and kitchen supplies",
    None, "6210", "339940", "office supplies")
RENT = service_product(
    "rent", "Office and yard rent, Køge", "Monthly rent for offices, workshop and yard",
    "months", "6220", "531ORE", "rent")
UTILITIES = service_product(
    "utilities", "Utilities on account", "Heating, water and electricity on account", None,
    "6220", "221100", "utilities")
OFFICE_CLEANING = service_product(
    "office-cleaning", "Office cleaning, monthly", "Cleaning of offices and canteen", "months",
    "6230", "561700", "cleaning")
CABIN_CLEANING = service_product(
    "cabin-cleaning", "Site cabin cleaning", "Cleaning of site welfare cabins, per visit",
    "visits", "6230", "561700", "cleaning")
LEGAL_ADVICE = service_product(
    "legal-advice", "Legal advice – contracts", "Contract review and negotiation support",
    "hours", "6310", "541100", "legal advice")
BOOKKEEPING = service_product(
    "bookkeeping", "Bookkeeping and payroll services",
    "Monthly bookkeeping, payroll and VAT returns", "months", "6320", "541200", "bookkeeping")
ANNUAL_AUDIT = service_product(
    "annual-audit", "Annual audit", "Statutory audit of the annual report", None, "6320",
    "541200", "audit")
STRUCTURAL_ENGINEERING = service_product(
    "structural-engineering", "Structural engineering",
    "Structural design, calculations and site supervision", "hours", "6330", "541300",
    "engineering consultancy")
VAN_LEASING = service_product(
    "van-leasing", "Van leasing, 12 vehicles", "Operational lease incl. service agreement",
    "months", "6410", "532100", "vehicle leasing")
VEHICLE_SERVICE = service_product(
    "vehicle-service", "Vehicle service and repair", "Scheduled service and repairs", None,
    "6420", "811100", "vehicle repair")
HOTEL_NIGHT = service_product(
    "hotel-night", "Hotel night, single room incl. breakfast", "Crew accommodation near site",
    "nights", "6610", "721000", "accommodation")
FLIGHT_CPH_AAL = service_product(
    "flight-cph-aal", "Flight Copenhagen–Aalborg, return", "Economy return ticket", "tickets",
    "6620", "481000", "air travel")
TRAIN_TICKETS = service_product(
    "train-tickets", "Train tickets", "Rail travel between sites and offices", None, "6620",
    "485000", "rail travel")
