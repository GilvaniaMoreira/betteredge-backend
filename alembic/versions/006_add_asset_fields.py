"""Add additional fields to assets table

Revision ID: 006
Revises: 005
Create Date: 2025-09-26 11:27:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to assets table
    op.add_column('assets', sa.Column('current_price', sa.Float(), nullable=True))
    op.add_column('assets', sa.Column('sector', sa.String(), nullable=True))
    op.add_column('assets', sa.Column('industry', sa.String(), nullable=True))
    op.add_column('assets', sa.Column('market_cap', sa.BigInteger(), nullable=True))
    op.add_column('assets', sa.Column('volume', sa.BigInteger(), nullable=True))
    op.add_column('assets', sa.Column('pe_ratio', sa.Float(), nullable=True))
    op.add_column('assets', sa.Column('dividend_yield', sa.Float(), nullable=True))
    op.add_column('assets', sa.Column('last_updated', sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    # Remove added columns
    op.drop_column('assets', 'last_updated')
    op.drop_column('assets', 'dividend_yield')
    op.drop_column('assets', 'pe_ratio')
    op.drop_column('assets', 'volume')
    op.drop_column('assets', 'market_cap')
    op.drop_column('assets', 'industry')
    op.drop_column('assets', 'sector')
    op.drop_column('assets', 'current_price')


