"""An item's class in its own column, and what a marketplace offer says of its product

Revision ID: 0024_item_class_and_offer_text
Revises: 0023_cheaper_alternatives
Create Date: 2026-10-02

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = '0024_item_class_and_offer_text'
down_revision = '0023_cheaper_alternatives'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('company_items', sa.Column('item_class', sa.String(), nullable=True))
    op.add_column('marketplace_offers', sa.Column('description', sa.String(), nullable=False,
                                                  server_default=''))


def downgrade() -> None:
    op.drop_column('marketplace_offers', 'description')
    op.drop_column('company_items', 'item_class')
