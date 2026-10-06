"""The demo company's spend tree and its ERP chart of accounts."""
from __future__ import annotations

from .shapes import AccountSpec, CategorySpec

TREE_NAME = "Nordlys Byg spend tree"
TREE_DEPTH = 3

DIRECT = "Direct"
INDIRECT = "Indirect"


def _leaf(group: tuple[str, str], name: str, code: str, description: str) -> CategorySpec:
    return CategorySpec(path=(*group, name), code=code, description=description)


MATERIALS = (DIRECT, "Building materials")
SUBCONTRACTORS = (DIRECT, "Subcontractors")
EQUIPMENT = (DIRECT, "Equipment hire")
ENERGY = (DIRECT, "Fuel & energy")
LOGISTICS = (DIRECT, "Freight & logistics")
IT = (INDIRECT, "IT & software")
OFFICE = (INDIRECT, "Office & facilities")
ADVISERS = (INDIRECT, "Professional services")
FLEET = (INDIRECT, "Vehicles & fleet")
SAFETY = (INDIRECT, "Workwear & safety")
TRAVEL = (INDIRECT, "Travel")

CATEGORIES: tuple[CategorySpec, ...] = (
    CategorySpec((DIRECT,), description="Spend that goes into the buildings the company delivers"),
    CategorySpec(MATERIALS, description="Materials built into the projects"),
    _leaf(MATERIALS, "Concrete & aggregates", "4110", "ready-mix concrete, aggregates and pumping"),
    _leaf(MATERIALS, "Timber & boards", "4120", "structural timber, OSB, plywood and boards"),
    _leaf(MATERIALS, "Steel & rebar", "4130", "reinforcing steel, mesh and structural steel"),
    _leaf(MATERIALS, "Insulation", "4140", "mineral wool and EPS insulation"),
    _leaf(MATERIALS, "Plumbing & electrical supplies", "4150",
          "pipes, fittings, cable and electrical fittings"),
    _leaf(MATERIALS, "Drywall & fixings", "4160", "gypsum boards, screws and fixings"),
    CategorySpec(SUBCONTRACTORS, description="Trades the company buys in"),
    _leaf(SUBCONTRACTORS, "Electrical installation", "4210", "electrical installation work"),
    _leaf(SUBCONTRACTORS, "Plumbing & heating", "4220", "plumbing and heating installation work"),
    _leaf(SUBCONTRACTORS, "Groundworks", "4230", "excavation, foundations and sewer works"),
    _leaf(SUBCONTRACTORS, "Scaffolding", "4240", "scaffolding hire, erection and dismantling"),
    CategorySpec(EQUIPMENT, description="Machinery and site equipment on hire"),
    _leaf(EQUIPMENT, "Earthmoving machinery", "4310", "excavators, loaders and telehandlers"),
    _leaf(EQUIPMENT, "Cranes & lifts", "4320", "mobile cranes and access platforms"),
    _leaf(EQUIPMENT, "Site cabins", "4330", "site cabins and welfare units"),
    CategorySpec(ENERGY, description="Fuel and power for sites and machines"),
    _leaf(ENERGY, "Diesel & fuel", "4410", "diesel and AdBlue for machines and vehicles"),
    _leaf(ENERGY, "Site electricity", "4420", "temporary power for construction sites"),
    CategorySpec(LOGISTICS, description="Getting materials to sites and waste away"),
    _leaf(LOGISTICS, "Haulage", "4510", "truck haulage and pallet deliveries"),
    _leaf(LOGISTICS, "Waste & skips", "4520", "skip hire and construction waste handling"),
    CategorySpec((INDIRECT,), description="Spend that runs the company"),
    CategorySpec(IT, description="Software, IT support and telecom"),
    _leaf(IT, "Software subscriptions", "6110", "software subscriptions and hosting"),
    _leaf(IT, "IT support", "6120", "managed IT support"),
    _leaf(IT, "Telecom", "6130", "mobile subscriptions and site connectivity"),
    CategorySpec(OFFICE, description="Running the office and yard"),
    _leaf(OFFICE, "Office supplies", "6210", "paper, toner and office supplies"),
    _leaf(OFFICE, "Rent & utilities", "6220", "office and yard rent with utilities"),
    _leaf(OFFICE, "Cleaning", "6230", "office and site cabin cleaning"),
    CategorySpec(ADVISERS, description="Advisers and consultants"),
    _leaf(ADVISERS, "Legal", "6310", "legal advice"),
    _leaf(ADVISERS, "Accounting & audit", "6320", "bookkeeping, payroll and audit"),
    _leaf(ADVISERS, "Engineering consultancy", "6330", "structural and building engineering"),
    CategorySpec(FLEET, description="The company's vans and cars"),
    _leaf(FLEET, "Vehicle leasing", "6410", "van and car leasing"),
    _leaf(FLEET, "Vehicle maintenance", "6420", "vehicle service, repairs and tyres"),
    CategorySpec(SAFETY, description="Keeping the crews safe and dressed"),
    _leaf(SAFETY, "Personal protective equipment", "6510",
          "gloves, helmets, hi-vis and safety boots"),
    _leaf(SAFETY, "Workwear", "6520", "work trousers and jackets"),
    CategorySpec(TRAVEL, description="Crews and staff travelling between sites"),
    _leaf(TRAVEL, "Hotels", "6610", "hotel nights for site crews"),
    _leaf(TRAVEL, "Flights & rail", "6620", "flights and train tickets"),
)

ACCOUNTS: tuple[AccountSpec, ...] = (
    AccountSpec("2010", "Building materials", "expense", True),
    AccountSpec("2020", "Subcontractors", "expense", True),
    AccountSpec("2030", "Equipment hire", "expense", True),
    AccountSpec("2040", "Fuel and energy", "expense", True),
    AccountSpec("2050", "Freight and waste", "expense", True),
    AccountSpec("2210", "IT and telecom", "expense", True),
    AccountSpec("2220", "Premises and office", "expense", True),
    AccountSpec("2230", "Advisers and fees", "expense", True),
    AccountSpec("2240", "Vehicles", "expense", True),
    AccountSpec("2250", "Workwear and safety", "expense", True),
    AccountSpec("2260", "Travel", "expense", True),
    AccountSpec("6820", "Input VAT", "liability", False),
    AccountSpec("6900", "Trade payables", "liability", False),
)

VAT_ACCOUNT = "6820"
PAYABLES_ACCOUNT = "6900"


def leaves() -> dict[str, CategorySpec]:
    """The leaves by their code."""
    return {category.code: category for category in CATEGORIES if category.code}
