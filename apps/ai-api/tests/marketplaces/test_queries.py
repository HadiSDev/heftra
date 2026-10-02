"""What marketplaces are asked about an item."""
from __future__ import annotations

from ai_api.marketplaces.queries import search_queries
from web_api.specs.attribute import Attribute
from web_api.specs.specification import Specification


def laptop(**changes) -> Specification:
    fields = dict(item_class="finished_good", product_type="laptop", name="MacBook Pro 14 M5 Pro",
                  brand="Apple", model="M5 Pro", pricing_unit="piece", attributes=[
                      Attribute(name="memory", kind="numeric", value="24", unit="GB"),
                      Attribute(name="storage", kind="numeric", value="1", unit="TB"),
                      Attribute(name="display", value="XDR")])
    fields.update(changes)
    return Specification(**fields)


def test_the_name_leads_with_the_brand_and_numbers_with_their_units():
    assert search_queries(laptop(), 2) == ["Apple MacBook Pro 14 M5 Pro 24 GB 1 TB"]


def test_a_model_the_name_lacks_is_added():
    assert search_queries(laptop(name="Laptop", attributes=[]), 2) == ["Apple Laptop M5 Pro"]


def test_the_part_number_is_asked_first():
    spec = laptop(part_number="MX2H3DK/A", attributes=[])
    assert search_queries(spec, 2) == ["Apple MX2H3DK/A", "Apple MacBook Pro 14 M5 Pro"]
    assert search_queries(spec, 1) == ["Apple MX2H3DK/A"]
