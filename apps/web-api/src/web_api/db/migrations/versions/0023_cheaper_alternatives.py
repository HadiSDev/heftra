"""Cheaper alternatives: stored items with their specifications, products, cached comparisons and
marketplace offers, items' alternatives, run parameters, and the price benchmark setting; the
unused recommendations table goes

Revision ID: 0023_cheaper_alternatives
Revises: 0022_scalable_agreement_analysis
Create Date: 2026-10-02

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = '0023_cheaper_alternatives'
down_revision = '0022_scalable_agreement_analysis'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('pipeline_runs', sa.Column('params', sa.JSON(), nullable=True))
    op.add_column('organizations', sa.Column('price_benchmark_enabled', sa.Boolean(),
                                             nullable=False, server_default=sa.true()))

    op.create_table(
        'products',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('gtin', sa.String(), nullable=True, unique=True),
        sa.Column('brand', sa.String(), nullable=True),
        sa.Column('part_number', sa.String(), nullable=True),
        sa.Column('model', sa.String(), nullable=True),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('item_class', sa.String(), nullable=False),
        sa.Column('pricing_unit', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=False),
    )
    op.create_index('ix_products_part_number', 'products', ['part_number'])

    op.create_table(
        'company_items',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('company_id', sa.String(), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('item_key', sa.String(), nullable=False),
        sa.Column('item_name', sa.String(), nullable=True),
        sa.Column('description', sa.String(), nullable=True),
        sa.Column('unit', sa.String(), nullable=True),
        sa.Column('vendor_id', sa.String(), sa.ForeignKey('vendors.id'), nullable=True),
        sa.Column('category_id', sa.String(), sa.ForeignKey('spend_categories.id'),
                  nullable=True),
        sa.Column('base_currency', sa.String(3), nullable=True),
        sa.Column('spend', sa.Numeric(16, 2), nullable=False),
        sa.Column('lines', sa.Integer(), nullable=False),
        sa.Column('last_bought_on', sa.Date(), nullable=True),
        sa.Column('line_quantity', sa.Numeric(18, 4), nullable=True),
        sa.Column('priced_spend', sa.Numeric(16, 2), nullable=True),
        sa.Column('order_quantity', sa.Numeric(14, 4), nullable=True),
        sa.Column('spec', sa.JSON(), nullable=True),
        sa.Column('spec_source', sa.String(), nullable=True),
        sa.Column('spec_text_hash', sa.String(), nullable=True),
        sa.Column('spec_failures', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('spec_signature', sa.String(), nullable=True),
        sa.Column('product_id', sa.String(), sa.ForeignKey('products.id'), nullable=True),
        sa.Column('quantity', sa.Numeric(18, 4), nullable=True),
        sa.Column('unit_price', sa.Numeric(18, 6), nullable=True),
        sa.Column('unit_price_eur', sa.Numeric(18, 6), nullable=True),
        sa.Column('price_note', sa.String(), nullable=True),
        sa.Column('searched_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('refreshed_at', sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint('company_id', 'item_key', name='uq_company_item'),
    )
    op.create_index('ix_company_items_company_id', 'company_items', ['company_id'])
    op.create_index('ix_company_items_spec_signature', 'company_items', ['spec_signature'])
    op.create_index('ix_company_items_product_id', 'company_items', ['product_id'])
    op.create_index('ix_company_items_company_spend', 'company_items', ['company_id', 'spend'])

    op.create_table(
        'spec_comparisons',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('kind', sa.String(), nullable=False),
        sa.Column('left_hash', sa.String(), nullable=False),
        sa.Column('right_hash', sa.String(), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('result', sa.JSON(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=False),
        sa.UniqueConstraint('kind', 'left_hash', 'right_hash', 'version',
                            name='uq_spec_comparison'),
    )

    op.create_table(
        'marketplace_queries',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('connector', sa.String(), nullable=False),
        sa.Column('market', sa.String(), nullable=False),
        sa.Column('query', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False),
        sa.Column('error', sa.String(), nullable=True),
        sa.Column('fetched_at', sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=False),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('connector', 'market', 'query', name='uq_marketplace_query'),
    )

    op.create_table(
        'marketplace_offers',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('query_id', sa.String(), sa.ForeignKey('marketplace_queries.id'),
                  nullable=False),
        sa.Column('connector', sa.String(), nullable=False),
        sa.Column('seller', sa.String(), nullable=False),
        sa.Column('url', sa.String(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('identifiers', sa.JSON(), nullable=False),
        sa.Column('spec', sa.JSON(), nullable=True),
        sa.Column('price', sa.Numeric(16, 4), nullable=False),
        sa.Column('price_breaks', sa.JSON(), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False),
        sa.Column('vat_included', sa.Boolean(), nullable=False),
        sa.Column('seller_country', sa.String(2), nullable=True),
        sa.Column('pack_quantity', sa.Numeric(14, 4), nullable=False),
        sa.Column('pack_unit', sa.String(), nullable=True),
        sa.Column('availability', sa.String(), nullable=True),
        sa.Column('shipping', sa.String(), nullable=True),
        sa.Column('seen_at', sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=False),
    )
    op.create_index('ix_marketplace_offers_query_id', 'marketplace_offers', ['query_id'])

    op.create_table(
        'item_alternatives',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('company_id', sa.String(), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('item_id', sa.String(), sa.ForeignKey('company_items.id'), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('match', sa.String(), nullable=False),
        sa.Column('ref_key', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('unit_price', sa.Numeric(18, 6), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False),
        sa.Column('saving_yearly', sa.Numeric(16, 2), nullable=True),
        sa.Column('saving_percent', sa.Numeric(7, 2), nullable=False),
        sa.Column('comparison', sa.JSON(), nullable=False),
        sa.Column('origin', sa.JSON(), nullable=False),
        sa.Column('agreement_notes', sa.JSON(), nullable=False),
        sa.Column('review_status', sa.String(), nullable=False),
        sa.Column('dismiss_reason', sa.String(), nullable=True),
        sa.Column('review_note', sa.String(), nullable=True),
        sa.Column('reviewed_by', sa.String(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('found_at', sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint('item_id', 'source', 'ref_key', name='uq_item_alternative'),
    )
    op.create_index('ix_item_alternatives_company_id', 'item_alternatives', ['company_id'])
    op.create_index('ix_item_alternatives_item_id', 'item_alternatives', ['item_id'])

    op.drop_table('recommendations')


def downgrade() -> None:
    op.create_table(
        'recommendations',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('company_id', sa.String(), sa.ForeignKey('companies.id'), nullable=False),
        sa.Column('rec_type', sa.String(), nullable=False),
        sa.Column('category_level_2', sa.String(), nullable=True),
        sa.Column('category_level_3', sa.String(), nullable=True),
        sa.Column('current_vendor_id', sa.String(), sa.ForeignKey('vendors.id'), nullable=True),
        sa.Column('current_vendor_name', sa.String(), nullable=True),
        sa.Column('annual_spend', sa.Numeric(14, 2), nullable=True),
        sa.Column('alternative_name', sa.String(), nullable=True),
        sa.Column('estimated_savings', sa.Numeric(14, 2), nullable=True),
        sa.Column('savings_pct', sa.Numeric(5, 2), nullable=True),
        sa.Column('confidence', sa.Numeric(4, 3), nullable=True),
        sa.Column('source', sa.String(), nullable=True),
        sa.Column('rationale', sa.String(), nullable=True),
        sa.Column('dismissed', sa.Boolean(), nullable=False),
        sa.Column('gt_savings', sa.Numeric(14, 2), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(),
                  nullable=False),
    )
    op.drop_index('ix_item_alternatives_item_id', table_name='item_alternatives')
    op.drop_index('ix_item_alternatives_company_id', table_name='item_alternatives')
    op.drop_table('item_alternatives')
    op.drop_index('ix_marketplace_offers_query_id', table_name='marketplace_offers')
    op.drop_table('marketplace_offers')
    op.drop_table('marketplace_queries')
    op.drop_table('spec_comparisons')
    op.drop_index('ix_company_items_company_spend', table_name='company_items')
    op.drop_index('ix_company_items_product_id', table_name='company_items')
    op.drop_index('ix_company_items_spec_signature', table_name='company_items')
    op.drop_index('ix_company_items_company_id', table_name='company_items')
    op.drop_table('company_items')
    op.drop_index('ix_products_part_number', table_name='products')
    op.drop_table('products')
    op.drop_column('organizations', 'price_benchmark_enabled')
    op.drop_column('pipeline_runs', 'params')
