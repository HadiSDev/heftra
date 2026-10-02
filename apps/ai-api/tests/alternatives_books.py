"""Organizations, companies and specified items, for alternatives tests."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlmodel import Session

from ai_api.alternatives.sources.found import ItemContext
from ai_api.specs.signature import signature
from spec_stub import spec
from web_api.db.models import Company, CompanyItem, Organization, Product, Vendor
from web_api.specs.specification import Specification

EUR = Decimal("0.134")


class Shelves:
    def __init__(self, session: Session) -> None:
        self.session = session

    def organization(self, name: str, *, benchmark: bool = True) -> Organization:
        organization = Organization(name=name, price_benchmark_enabled=benchmark)
        self.session.add(organization)
        self.session.commit()
        return organization

    def company(self, organization: Organization, name: str = "Co",
                currency: str = "DKK") -> Company:
        company = Company(organization_id=organization.id, name=name, base_currency=currency)
        self.session.add(company)
        self.session.commit()
        return company

    def vendor(self, name: str) -> Vendor:
        vendor = Vendor(name=name, country_code="DK")
        self.session.add(vendor)
        self.session.commit()
        return vendor

    def product(self, part_number: str) -> Product:
        product = Product(part_number=part_number, name=part_number, item_class="finished_good",
                          pricing_unit="piece")
        self.session.add(product)
        self.session.commit()
        return product

    def item(self, company: Company, name: str, *, unit_price: str, quantity: str = "10",
             fields: dict | None = None, product: Product | None = None,
             vendor: Vendor | None = None) -> CompanyItem:
        specification = Specification.model_validate(spec(name, **(fields or {})))
        price = Decimal(unit_price)
        item = CompanyItem(
            company_id=company.id, item_key=f"{company.id}:{name}:{unit_price}", item_name=name,
            base_currency=company.base_currency, lines=1, spend=price * Decimal(quantity),
            last_bought_on=date(2026, 5, 1), spec=specification.stored(), spec_source="ai",
            item_class=specification.item_class.value, spec_signature=signature(specification),
            product_id=product.id if product else None, vendor_id=vendor.id if vendor else None,
            quantity=Decimal(quantity), unit_price=price, unit_price_eur=price * EUR)
        self.session.add(item)
        self.session.commit()
        return item

    def context(self, item: CompanyItem) -> ItemContext:
        company = self.session.get(Company, item.company_id)
        return ItemContext(item=item, spec=Specification.model_validate(item.spec),
                           organization_id=company.organization_id,
                           base_currency=company.base_currency, eur_rate=EUR)
