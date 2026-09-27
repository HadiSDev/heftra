"""Background imports of emission factor workbooks and price indices

Revision ID: 0019_reference_data_imports
Revises: 0018_price_indices
Create Date: 2026-09-27

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = '0019_reference_data_imports'
down_revision = '0018_price_indices'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'reference_data_imports',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('kind', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('subject', sa.String(), nullable=False),
        sa.Column('activate', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column('requested_by', sa.String(), nullable=False),
        sa.Column(
            'requested_at', sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False,
        ),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('finished_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('result', sa.JSON(), nullable=True),
        sa.Column('error', sa.String(), nullable=True),
    )
    op.create_index(
        'ix_reference_data_imports_requested', 'reference_data_imports', ['requested_at'],
    )
    op.create_index(
        'ix_reference_data_imports_kind_status', 'reference_data_imports', ['kind', 'status'],
    )


def downgrade() -> None:
    op.drop_index('ix_reference_data_imports_kind_status', table_name='reference_data_imports')
    op.drop_index('ix_reference_data_imports_requested', table_name='reference_data_imports')
    op.drop_table('reference_data_imports')
