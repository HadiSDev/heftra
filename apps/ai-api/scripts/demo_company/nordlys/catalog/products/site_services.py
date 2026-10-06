"""Services bought for the sites: trades, machine hire, power, haulage and waste."""
from __future__ import annotations

from .builders import service_product


CONCRETE_PUMPING = service_product(
    "concrete-pumping", "Concrete pump hire incl. operator",
    "Truck-mounted boom pump 36 m with operator", "hours", "4110", "532400", "concrete pumping")
ELECTRICIAN_HOURS = service_product(
    "electrician-hours", "Electrical installation – labour",
    "Electricians on site, hours as per approved timesheets", "hours", "4210", "2332A0",
    "electrical installation")
ELECTRICAL_MATERIALS = service_product(
    "electrical-materials", "Electrical installation – materials",
    "Cable trays, consumables and small fittings used on site", None, "4210", "2332A0",
    "electrical installation")
PLUMBER_HOURS = service_product(
    "plumber-hours", "Plumbing and heating – labour",
    "Plumbers on site, hours as per approved timesheets", "hours", "4220", "233412",
    "plumbing installation")
HEATING_MATERIALS = service_product(
    "heating-materials", "Plumbing and heating – materials",
    "Radiators, manifolds and fittings used on site", None, "4220", "233412",
    "plumbing installation")
GROUNDWORKS_STAGE = service_product(
    "groundworks-stage", "Groundworks – stage payment",
    "Excavation, foundations and drainage as per the agreed stage plan", None, "4230", "2332D0",
    "groundworks")
SEWER_CONNECTION = service_product(
    "sewer-connection", "Sewer connection works",
    "Connection of building drainage to the public sewer", None, "4230", "2332D0", "groundworks")
SCAFFOLD_HIRE = service_product(
    "scaffold-hire", "Scaffolding hire, per week", "Facade scaffolding incl. weekly inspection",
    "weeks", "4240", "532400", "scaffolding hire")
SCAFFOLD_ERECTION = service_product(
    "scaffold-erection", "Scaffolding erection and dismantling",
    "Erection and dismantling crew", None, "4240", "532400", "scaffolding")
EXCAVATOR_5T = service_product(
    "excavator-5t", "Mini excavator 5 t hire", "Mini excavator 5 t with buckets, per day",
    "days", "4310", "532400", "machine hire")
LOADER_8T = service_product(
    "loader-8t", "Wheel loader 8 t hire", "Wheel loader 8 t with pallet forks, per day", "days",
    "4310", "532400", "machine hire")
TELEHANDLER_14M = service_product(
    "telehandler-14m", "Telehandler 14 m hire", "Telehandler 14 m, 4 t, per day", "days", "4310",
    "532400", "machine hire")
CRANE_60T = service_product(
    "crane-60t", "Mobile crane 60 t incl. operator", "Mobile crane 60 t with operator, per hour",
    "hours", "4320", "532400", "crane hire")
SCISSOR_LIFT = service_product(
    "scissor-lift-12m", "Scissor lift 12 m hire", "Electric scissor lift 12 m, per day", "days",
    "4320", "532400", "access platform hire")
SITE_CABIN = service_product(
    "site-cabin", "Site cabin 20 ft hire",
    "Welfare cabin with canteen and drying room, per month", "months", "4330", "532A00",
    "site cabin hire")
SITE_POWER = service_product(
    "site-power", "Temporary site electricity", "Metered construction site power", "kWh", "4420",
    "221100", "electricity")
HAULAGE = service_product(
    "haulage-crane-truck", "Haulage, 18 t truck with crane", "Truck with loader crane, per hour",
    "hours", "4510", "484000", "haulage")
PALLET_DELIVERY = service_product(
    "pallet-delivery", "Pallet delivery, Zealand", "Next-day pallet delivery to site", "pallets",
    "4510", "484000", "haulage")
SKIP_HIRE = service_product(
    "skip-10m3", "Skip hire 10 m³, mixed construction waste",
    "Delivery, exchange and collection of a 10 m³ skip", "skips", "4520", "562000",
    "waste collection")
WASTE_HANDLING = service_product(
    "waste-handling", "Waste handling fee", "Sorting and disposal of mixed construction waste",
    "t", "4520", "562000", "waste handling")
