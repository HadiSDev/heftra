"""Trade agreements, their terms, the findings against them, and the scope judgement cache

Revision ID: 0020_trade_agreements
Revises: 0019_reference_data_imports
Create Date: 2026-09-27

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = '0020_trade_agreements'
down_revision = '0019_reference_data_imports'
branch_labels = None
depends_on = None


def _created_at() -> sa.Column:
    return sa.Column(
        'created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False,
    )


def upgrade() -> None:
    op.create_table(
        'agreements',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('company_id', sa.String(), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('file_id', sa.String(), sa.ForeignKey('files.id'), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('reference', sa.String(), nullable=True),
        sa.Column('vendor_id', sa.String(), sa.ForeignKey('vendors.id'), nullable=True),
        sa.Column('supplier_name', sa.String(), nullable=True),
        sa.Column('supplier_vat_number', sa.String(), nullable=True),
        sa.Column('supplier_website', sa.String(), nullable=True),
        sa.Column('starts_on', sa.Date(), nullable=True),
        sa.Column('ends_on', sa.Date(), nullable=True),
        sa.Column('currency', sa.String(3), nullable=True),
        sa.Column('summary', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('read_attempts', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('read_error', sa.String(), nullable=True),
        sa.Column('read_started_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('analysed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('uploaded_by', sa.String(), nullable=False),
        _created_at(),
    )
    op.create_index('ix_agreements_company_id', 'agreements', ['company_id'])
    op.create_index('ix_agreements_status', 'agreements', ['status'])

    op.create_table(
        'agreement_terms',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('agreement_id', sa.String(), sa.ForeignKey('agreements.id'), nullable=False),
        sa.Column('kind', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('scope', sa.String(), nullable=False),
        sa.Column('conditions', sa.String(), nullable=True),
        sa.Column('item', sa.String(), nullable=True),
        sa.Column('unit', sa.String(), nullable=True),
        sa.Column('unit_price', sa.Numeric(14, 4), nullable=True),
        sa.Column('discount_percent', sa.Numeric(6, 3), nullable=True),
        sa.Column('commitment_amount', sa.Numeric(14, 2), nullable=True),
        sa.Column('commitment_period', sa.String(), nullable=True),
        sa.Column('tiers', sa.JSON(), nullable=True),
        sa.Column('currency', sa.String(3), nullable=True),
        sa.Column('scope_category_ids', sa.JSON(), nullable=False),
        sa.Column('quotes', sa.JSON(), nullable=False),
        sa.Column('confidence', sa.Numeric(4, 3), nullable=True),
        _created_at(),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_agreement_terms_agreement_id', 'agreement_terms', ['agreement_id'])

    op.create_table(
        'agreement_findings',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('company_id', sa.String(), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('agreement_id', sa.String(), sa.ForeignKey('agreements.id'), nullable=False),
        sa.Column('term_id', sa.String(), sa.ForeignKey('agreement_terms.id'), nullable=False),
        sa.Column(
            'invoice_line_id', sa.String(), sa.ForeignKey('invoice_lines.id'), nullable=False,
        ),
        sa.Column('invoice_id', sa.String(), sa.ForeignKey('invoices.id'), nullable=False),
        sa.Column('vendor_id', sa.String(), sa.ForeignKey('vendors.id'), nullable=True),
        sa.Column('kind', sa.String(), nullable=False),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('amount', sa.Numeric(14, 2), nullable=False),
        sa.Column('line_amount', sa.Numeric(14, 2), nullable=False),
        sa.Column('from_supplier', sa.Boolean(), nullable=False),
        sa.Column('currency', sa.String(3), nullable=True),
        sa.Column('expected', sa.Numeric(14, 4), nullable=True),
        sa.Column('actual', sa.Numeric(14, 4), nullable=True),
        sa.Column('quantity', sa.Numeric(12, 4), nullable=True),
        sa.Column('reason', sa.String(), nullable=False),
        sa.Column('judge_confidence', sa.Numeric(4, 3), nullable=True),
        sa.Column('spent_on', sa.Date(), nullable=True),
        sa.Column('computed_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('review_status', sa.String(), nullable=False),
        sa.Column('review_note', sa.String(), nullable=True),
        sa.Column('reviewed_by', sa.String(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('term_id', 'invoice_line_id', 'kind', name='uq_agreement_finding'),
    )
    op.create_index('ix_agreement_findings_company_id', 'agreement_findings', ['company_id'])
    op.create_index('ix_agreement_findings_agreement_id', 'agreement_findings', ['agreement_id'])

    op.create_table(
        'agreement_scope_judgements',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('term_id', sa.String(), sa.ForeignKey('agreement_terms.id'), nullable=False),
        sa.Column('term_key', sa.String(), nullable=False),
        sa.Column('question_key', sa.String(), nullable=False),
        sa.Column('in_scope', sa.Boolean(), nullable=False),
        sa.Column('same_item', sa.Boolean(), nullable=True),
        sa.Column('units_comparable', sa.Boolean(), nullable=True),
        sa.Column('confidence', sa.Numeric(4, 3), nullable=True),
        sa.Column('reason', sa.String(), nullable=False),
        _created_at(),
        sa.UniqueConstraint(
            'term_id', 'term_key', 'question_key', name='uq_agreement_scope_judgement',
        ),
    )
    op.create_index(
        'ix_agreement_scope_judgements_term_id', 'agreement_scope_judgements', ['term_id'],
    )


def downgrade() -> None:
    op.drop_index('ix_agreement_scope_judgements_term_id', table_name='agreement_scope_judgements')
    op.drop_table('agreement_scope_judgements')
    op.drop_index('ix_agreement_findings_agreement_id', table_name='agreement_findings')
    op.drop_index('ix_agreement_findings_company_id', table_name='agreement_findings')
    op.drop_table('agreement_findings')
    op.drop_index('ix_agreement_terms_agreement_id', table_name='agreement_terms')
    op.drop_table('agreement_terms')
    op.drop_index('ix_agreements_status', table_name='agreements')
    op.drop_index('ix_agreements_company_id', table_name='agreements')
    op.drop_table('agreements')
