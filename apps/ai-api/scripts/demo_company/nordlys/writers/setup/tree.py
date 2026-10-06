"""The demo company's own spend tree."""
from __future__ import annotations

from sqlmodel import Session

from web_api.db.models import SpendCategory, SpendTree, SpendTreeSource

from ...catalog.tree import CATEGORIES, TREE_DEPTH, TREE_NAME
from ...ids import TREE_ID, demo_id
from ...settings import ORGANIZATION_ID

LEVEL_FIELDS = ("level_1", "level_2", "level_3", "level_4")


def write_tree(session: Session) -> dict[str, SpendCategory]:
    """Create the tree and its categories; returns the leaves by code."""
    session.add(SpendTree(id=TREE_ID, organization_id=ORGANIZATION_ID, name=TREE_NAME,
                          max_depth=TREE_DEPTH, source=SpendTreeSource.CUSTOM))
    session.flush()
    by_path: dict[tuple[str, ...], SpendCategory] = {}
    siblings: dict[tuple[str, ...], int] = {}
    for spec in sorted(CATEGORIES, key=lambda category: len(category.path)):
        parent_path = spec.path[:-1]
        parent = by_path.get(parent_path)
        order = siblings.get(parent_path, 0)
        siblings[parent_path] = order + 1
        category = SpendCategory(
            id=demo_id("spend-category", "/".join(spec.path)), spend_tree_id=TREE_ID,
            parent_id=parent.id if parent is not None else None, depth=len(spec.path),
            name=spec.path[-1], code=spec.code, sort_order=order, description=spec.description)
        for index, field in enumerate(LEVEL_FIELDS):
            setattr(category, field, spec.path[index] if index < len(spec.path) else None)
        session.add(category)
        session.flush()
        by_path[spec.path] = category
    return {category.code: category for category in by_path.values() if category.code}
