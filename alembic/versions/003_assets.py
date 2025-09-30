"""Create assets table

Revision ID: 003
Revises: 002
Create Date: 2025-09-30 10:45:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create assets table
    op.create_table('assets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('ticker', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('exchange', sa.String(), nullable=True),
        sa.Column('currency', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_assets_id'), 'assets', ['id'], unique=False)
    op.create_index(op.f('ix_assets_ticker'), 'assets', ['ticker'], unique=True)


def downgrade() -> None:
    op.drop_index(op.f('ix_assets_ticker'), table_name='assets')
    op.drop_index(op.f('ix_assets_id'), table_name='assets')
    op.drop_table('assets')
