"""Emission factor sets, their sectors and factors, and each line's emission sector

Revision ID: 0017_emissions
Revises: 0016_document_supplier_identity
Create Date: 2026-09-27

"""
from __future__ import annotations

from alembic import op
import sqlalchemy as sa

revision = '0017_emissions'
down_revision = '0016_document_supplier_identity'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'emission_factor_sets',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('version', sa.String(), nullable=False),
        sa.Column('classification', sa.String(), nullable=False),
        sa.Column('currency', sa.String(3), nullable=False),
        sa.Column('price_year', sa.Integer(), nullable=False),
        sa.Column('price_basis', sa.String(), nullable=False),
        sa.Column('licence', sa.String(), nullable=False),
        sa.Column('attribution', sa.String(), nullable=False),
        sa.Column('active', sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            'imported_at', sa.DateTime(timezone=True),
            server_default=sa.func.now(), nullable=False,
        ),
        sa.UniqueConstraint('source', 'version', name='uq_emission_factor_set_version'),
    )
    op.create_table(
        'emission_sectors',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('classification', sa.String(), nullable=False),
        sa.Column('code', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.String(), nullable=True),
        sa.UniqueConstraint('classification', 'code', name='uq_emission_sector_code'),
    )
    op.create_index('ix_emission_sectors_classification', 'emission_sectors', ['classification'])
    op.create_table(
        'emission_factors',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column(
            'factor_set_id', sa.String(), sa.ForeignKey('emission_factor_sets.id'), nullable=False,
        ),
        sa.Column('sector_id', sa.String(), sa.ForeignKey('emission_sectors.id'), nullable=False),
        sa.Column('country_code', sa.String(2), nullable=True),
        sa.Column('region', sa.String(), nullable=True),
        sa.Column('kg_co2e_per_unit', sa.Numeric(18, 8), nullable=False),
        sa.CheckConstraint(
            '(country_code IS NULL) <> (region IS NULL)', name='ck_emission_factor_one_area',
        ),
    )
    op.create_index('ix_emission_factors_factor_set_id', 'emission_factors', ['factor_set_id'])
    op.create_index(
        'uq_emission_factor_country', 'emission_factors',
        ['factor_set_id', 'sector_id', 'country_code'],
        unique=True, postgresql_where=sa.text('country_code IS NOT NULL'),
    )
    op.create_index(
        'uq_emission_factor_region', 'emission_factors',
        ['factor_set_id', 'sector_id', 'region'],
        unique=True, postgresql_where=sa.text('region IS NOT NULL'),
    )
    op.create_table(
        'emission_country_regions',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column(
            'factor_set_id', sa.String(), sa.ForeignKey('emission_factor_sets.id'), nullable=False,
        ),
        sa.Column('country_code', sa.String(2), nullable=False),
        sa.Column('region', sa.String(), nullable=False),
        sa.UniqueConstraint('factor_set_id', 'country_code', name='uq_emission_country_region'),
    )
    op.create_index(
        'ix_emission_country_regions_factor_set_id', 'emission_country_regions', ['factor_set_id'],
    )
    op.add_column(
        'invoice_lines',
        sa.Column(
            'emission_sector_id', sa.String(), sa.ForeignKey('emission_sectors.id'), nullable=True,
        ),
    )
    op.add_column('invoice_lines', sa.Column('emission_sector_source', sa.String(), nullable=True))
    op.add_column(
        'invoice_lines', sa.Column('emission_sector_confidence', sa.Numeric(4, 3), nullable=True),
    )
    op.add_column(
        'invoice_lines', sa.Column('emission_sector_rationale', sa.String(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column('invoice_lines', 'emission_sector_rationale')
    op.drop_column('invoice_lines', 'emission_sector_confidence')
    op.drop_column('invoice_lines', 'emission_sector_source')
    op.drop_column('invoice_lines', 'emission_sector_id')
    op.drop_index(
        'ix_emission_country_regions_factor_set_id', table_name='emission_country_regions',
    )
    op.drop_table('emission_country_regions')
    op.drop_index('uq_emission_factor_region', table_name='emission_factors')
    op.drop_index('uq_emission_factor_country', table_name='emission_factors')
    op.drop_index('ix_emission_factors_factor_set_id', table_name='emission_factors')
    op.drop_table('emission_factors')
    op.drop_index('ix_emission_sectors_classification', table_name='emission_sectors')
    op.drop_table('emission_sectors')
    op.drop_table('emission_factor_sets')
