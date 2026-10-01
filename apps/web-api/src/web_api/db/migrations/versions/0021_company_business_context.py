"""What a company does: its website and a description, researched or written by a manager

Revision ID: 0021_company_business_context
Revises: 0020_trade_agreements
Create Date: 2026-10-01

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = '0021_company_business_context'
down_revision = '0020_trade_agreements'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('companies', sa.Column('website', sa.String(), nullable=True))
    op.add_column('companies', sa.Column('description', sa.String(), nullable=True))
    op.add_column('companies', sa.Column('description_source', sa.String(), nullable=True))
    op.add_column('companies', sa.Column('researched_at', sa.DateTime(timezone=True),
                                         nullable=True))


def downgrade() -> None:
    op.drop_column('companies', 'researched_at')
    op.drop_column('companies', 'description_source')
    op.drop_column('companies', 'description')
    op.drop_column('companies', 'website')
