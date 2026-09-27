"""Monthly price index values, for deflating spend to an emission factor's price year

Revision ID: 0018_price_indices
Revises: 0017_emissions
Create Date: 2026-09-27

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = '0018_price_indices'
down_revision = '0017_emissions'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'price_index_values',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('series', sa.String(), nullable=False),
        sa.Column('month', sa.Date(), nullable=False),
        sa.Column('value', sa.Numeric(14, 4), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column(
            'imported_at', sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False,
        ),
        sa.UniqueConstraint('series', 'month', name='uq_price_index_value_month'),
    )


def downgrade() -> None:
    op.drop_table('price_index_values')
