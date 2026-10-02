"""Analysing agreements incrementally: when what lines and invoices say changed, what a line bought,
each agreement's watermark, and the terms' monthly spend

Revision ID: 0022_scalable_agreement_analysis
Revises: 0021_company_business_context
Create Date: 2026-10-02

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = '0022_scalable_agreement_analysis'
down_revision = '0021_company_business_context'
branch_labels = None
depends_on = None


def upgrade() -> None:
    for table in ('invoice_lines', 'invoices'):
        op.add_column(table, sa.Column('changed_at', sa.DateTime(timezone=True),
                                       server_default=sa.func.now(), nullable=True))
        op.execute(f"UPDATE {table} SET changed_at = created_at")
        op.alter_column(table, 'changed_at', nullable=False)
        op.create_index(f'ix_{table}_company_changed', table, ['company_id', 'changed_at'])

    op.add_column('invoice_lines', sa.Column('item_key', sa.String(), nullable=True))
    op.create_index('ix_invoice_lines_company_item', 'invoice_lines', ['company_id', 'item_key'])

    op.add_column('agreements', sa.Column('analysed_from', sa.DateTime(timezone=True),
                                          nullable=True))
    op.add_column('agreements', sa.Column('full_analysis', sa.Boolean(), nullable=False,
                                          server_default=sa.false()))
    op.execute("UPDATE agreements SET full_analysis = true")

    op.create_table(
        'agreement_term_spend',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('term_id', sa.String(), sa.ForeignKey('agreement_terms.id'), nullable=False),
        sa.Column('month', sa.Date(), nullable=False),
        sa.Column('from_supplier', sa.Boolean(), nullable=False),
        sa.Column('amount', sa.Numeric(16, 2), nullable=False),
        sa.Column('lines', sa.Integer(), nullable=False),
        sa.UniqueConstraint('term_id', 'month', 'from_supplier', name='uq_agreement_term_spend'),
    )
    op.create_index('ix_agreement_term_spend_term_id', 'agreement_term_spend', ['term_id'])


def downgrade() -> None:
    op.drop_index('ix_agreement_term_spend_term_id', table_name='agreement_term_spend')
    op.drop_table('agreement_term_spend')
    op.drop_column('agreements', 'full_analysis')
    op.drop_column('agreements', 'analysed_from')
    op.drop_index('ix_invoice_lines_company_item', table_name='invoice_lines')
    op.drop_column('invoice_lines', 'item_key')
    for table in ('invoices', 'invoice_lines'):
        op.drop_index(f'ix_{table}_company_changed', table_name=table)
        op.drop_column(table, 'changed_at')
