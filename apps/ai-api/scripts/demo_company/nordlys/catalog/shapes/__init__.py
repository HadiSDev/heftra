"""The shapes the demo company's catalog is written in."""
from .agreement import AgreementSpec, TermSpec
from .alternative import AlternativeSpec
from .category import AccountSpec, CategorySpec
from .milestone import MilestoneSpec
from .offer import OfferSpec, PricePoint
from .product import ProductSpec
from .supplier import Billing, SupplierSpec

__all__ = [
    "AccountSpec",
    "AgreementSpec",
    "AlternativeSpec",
    "Billing",
    "CategorySpec",
    "MilestoneSpec",
    "OfferSpec",
    "PricePoint",
    "ProductSpec",
    "SupplierSpec",
    "TermSpec",
]
