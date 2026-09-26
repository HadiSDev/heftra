"""Sectors, a line context and an index for the matchers' tests."""
from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from qdrant_client import QdrantClient

from ai_api.emissions.line_context import LineContext
from ai_api.emissions.sector_index import SectorIndex
from web_api.db.models import EmissionSector

VOCAB = ["hosting", "software", "flight", "legal"]


def fake_embed(texts):
    return [[float(text.lower().count(word)) + 0.01 for word in VOCAB] for text in texts]


def sectors() -> list[EmissionSector]:
    return [
        EmissionSector(id=str(uuid4()), classification="ceda-bea", code="518200",
                       name="Data processing, hosting", description="Hosting and data centres."),
        EmissionSector(id=str(uuid4()), classification="ceda-bea", code="511200",
                       name="Software publishers", description="Publishing software."),
    ]


def index_of(all_sectors: list[EmissionSector]) -> SectorIndex:
    index = SectorIndex(QdrantClient(location=":memory:"), fake_embed)
    index.ensure("ceda-bea", all_sectors)
    return index


def context(**overrides) -> LineContext:
    fields = dict(
        line_id="line-1", item_name="Dedicated server AX41", description=None,
        amount=Decimal("39.00"), currency="EUR",
        category_path=["Indirect", "Technology", "Cloud & Hosting"],
        supplier_name="Hetzner Online GmbH", supplier_country="DE",
        supplier_description="German hosting company.", supplier_website="https://hetzner.com",
        other_lines=["Backup space"],
    )
    fields.update(overrides)
    return LineContext(**fields)
