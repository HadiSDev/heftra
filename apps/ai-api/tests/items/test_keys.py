"""Which lines bought the same item."""
from __future__ import annotations

from web_api.items.keys import item_key, item_text


def test_case_and_spacing_do_not_make_another_item():
    assert item_key(" Magic  Keyboard ", None, "Piece", "c1", "v1") == item_key(
        "magic keyboard", "", "piece", "c1", "v1")


def test_another_supplier_or_category_is_another_item():
    key = item_key("Magic Keyboard", None, "piece", "c1", "v1")
    assert key != item_key("Magic Keyboard", None, "piece", "c1", "v2")
    assert key != item_key("Magic Keyboard", None, "piece", "c2", "v1")


def test_an_item_reads_as_its_name_and_detail():
    assert item_text("Magic Keyboard", "Danish layout") == "Magic Keyboard — Danish layout"
    assert item_text("Magic Keyboard", "magic keyboard") == "Magic Keyboard"
    assert item_text(None, None) == "(no description)"
