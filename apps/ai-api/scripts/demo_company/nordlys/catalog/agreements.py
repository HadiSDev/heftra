"""The two framework agreements the demo company works under, with the text of their PDFs."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from .shapes import AgreementSpec, TermSpec
from .suppliers.materials import CONCRETE_AGREEMENT_START, REBAR_AGREEMENT_START

PREFERRED_SUPPLIER = "preferred_supplier"
AGREED_PRICE = "agreed_price"
DISCOUNT = "discount"
VOLUME_COMMITMENT = "volume_commitment"

CONCRETE_PREFERRED = ("Nordlys Byg shall purchase all ready-mix concrete for its projects on "
                      "Zealand and Funen from Nordisk Beton.")
CONCRETE_PRICE = "Ready-mix concrete C30/37 (XC3, Dmax 16, S3): EUR 126.00 per m³ delivered."
CONCRETE_PUMPING = "Concrete pumping is invoiced with a discount of 8 percent off list price."
CONCRETE_VOLUME = ("Nordlys Byg commits to purchases of ready-mix concrete of at least "
                   "EUR 900,000 per contract year.")

REBAR_PREFERRED = ("Reinforcing steel, including bars and welded mesh, shall be ordered from "
                   "Jernlager Danmark.")
REBAR_PRICE = "Rebar B500B Ø12 mm in 12 m lengths: EUR 1,010.00 per tonne."
REBAR_MESH = "Welded reinforcement mesh carries a discount of 5 percent off list price."

CONCRETE = AgreementSpec(
    key="nordisk-beton-2026",
    title="Framework Agreement – Ready-Mix Concrete 2026–2027",
    reference="NB-FA-2026-014",
    supplier="nordisk-beton",
    starts_on=CONCRETE_AGREEMENT_START,
    ends_on=date(2027, 12, 31),
    summary=("Two-year framework agreement making Nordisk Beton the preferred supplier of "
             "ready-mix concrete on Zealand and Funen, with a fixed price for C30/37, 8% off "
             "concrete pumping and a yearly volume commitment of EUR 900,000 with rebates."),
    filename="Nordisk Beton – Framework Agreement 2026-2027.pdf",
    uploaded_on=date(2026, 1, 22),
    terms=(
        TermSpec("preferred", PREFERRED_SUPPLIER, "Ready-mix concrete",
                 ("concrete-c3037", "concrete-c2530"), ("4110",), CONCRETE_PREFERRED, 2,
                 confidence=Decimal("0.96")),
        TermSpec("c3037-price", AGREED_PRICE, "Ready-mix concrete C30/37", ("concrete-c3037",),
                 ("4110",), CONCRETE_PRICE, 3, item="Ready-mix concrete C30/37", unit="m3",
                 unit_price=Decimal("126.00"), confidence=Decimal("0.97")),
        TermSpec("pumping-discount", DISCOUNT, "Concrete pumping", ("concrete-pumping",),
                 ("4110",), CONCRETE_PUMPING, 3, discount_percent=Decimal("8"),
                 confidence=Decimal("0.93")),
        TermSpec("volume", VOLUME_COMMITMENT, "Ready-mix concrete",
                 ("concrete-c3037", "concrete-c2530"), ("4110",), CONCRETE_VOLUME, 4,
                 commitment_amount=Decimal("900000"), commitment_period="year",
                 tiers=({"threshold": 750000, "rebate_percent": 1.5},
                        {"threshold": 1000000, "rebate_percent": 2.5}),
                 confidence=Decimal("0.91")),
    ),
    pages=(
        ("FRAMEWORK AGREEMENT NB-FA-2026-014", "",
         "between Nordlys Byg A/S (VAT DK40012345), Køge",
         "and Nordisk Beton ApS, Køge",
         "", "Supply of ready-mix concrete and concrete pumping",
         "Term: 1 February 2026 to 31 December 2027. All prices in EUR excluding VAT."),
        ("2. Purchasing obligation", CONCRETE_PREFERRED,
         "Exceptions require written approval from the Nordlys Byg purchasing manager."),
        ("3. Prices and discounts", CONCRETE_PRICE,
         "Ready-mix concrete C25/30 and other recipes at the supplier's list price.",
         CONCRETE_PUMPING),
        ("4. Volume and rebates", CONCRETE_VOLUME,
         "A rebate of 1.5% applies from EUR 750,000 and 2.5% from EUR 1,000,000 per year.",
         "", "Signed for Nordlys Byg A/S and Nordisk Beton ApS, 20 January 2026."),
    ),
)

REBAR = AgreementSpec(
    key="jernlager-danmark-2025",
    title="Supply Agreement – Reinforcing Steel",
    reference="JD-2025-221",
    supplier="jernlager-danmark",
    starts_on=REBAR_AGREEMENT_START,
    ends_on=date(2026, 12, 31),
    summary=("Supply agreement for reinforcing steel with Jernlager Danmark as preferred "
             "supplier, a fixed price for Ø12 mm rebar and 5% off welded mesh."),
    filename="Jernlager Danmark – Supply Agreement Reinforcing Steel.pdf",
    uploaded_on=date(2025, 9, 18),
    terms=(
        TermSpec("preferred", PREFERRED_SUPPLIER, "Reinforcing steel (bars and mesh)",
                 ("rebar-12", "rebar-10", "mesh-k131"), ("4130",), REBAR_PREFERRED, 1,
                 confidence=Decimal("0.95")),
        TermSpec("rebar-12-price", AGREED_PRICE, "Rebar B500B Ø12 mm", ("rebar-12",), ("4130",),
                 REBAR_PRICE, 2, item="Rebar B500B Ø12 mm", unit="t",
                 unit_price=Decimal("1010.00"), confidence=Decimal("0.97")),
        TermSpec("mesh-discount", DISCOUNT, "Welded reinforcement mesh", ("mesh-k131",),
                 ("4130",), REBAR_MESH, 2, discount_percent=Decimal("5"),
                 confidence=Decimal("0.92")),
    ),
    pages=(
        ("SUPPLY AGREEMENT JD-2025-221", "",
         "between Nordlys Byg A/S (VAT DK40012345), Køge",
         "and Jernlager Danmark A/S, Vejle",
         "", "Term: 1 October 2025 to 31 December 2026. Prices in EUR excluding VAT.",
         "", "1. Scope", REBAR_PREFERRED),
        ("2. Prices", REBAR_PRICE, "Other diameters at the supplier's list price.", REBAR_MESH,
         "", "Signed for Nordlys Byg A/S and Jernlager Danmark A/S, 15 September 2025."),
    ),
)

AGREEMENTS = (CONCRETE, REBAR)
