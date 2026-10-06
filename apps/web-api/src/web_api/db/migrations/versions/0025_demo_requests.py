"""Demo requests submitted from the landing site

Revision ID: 0025_demo_requests
Revises: 0024_item_class_and_offer_text
Create Date: 2026-10-03

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = '0025_demo_requests'
down_revision = '0024_item_class_and_offer_text'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'demo_requests',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('company', sa.String(), nullable=False),
        sa.Column('company_size', sa.String(), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('consented_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('source_ip', sa.String(), nullable=True),
        sa.Column('user_agent', sa.String(), nullable=True),
        sa.Column(
            'created_at', sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False,
        ),
    )


def downgrade() -> None:
    op.drop_table('demo_requests')
