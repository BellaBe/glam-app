"""Create credit accounts and transactions tables

Revision ID: 001_initial_credit_tables
Revises: 
Create Date: 2025-10-18

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = '001_initial_credit_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create credit_accounts table
    op.create_table(
        'credit_accounts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('merchant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('platform_name', sa.String(255), nullable=False),
        sa.Column('platform_id', sa.String(255), nullable=False),
        sa.Column('platform_domain', sa.String(255), nullable=False),
        sa.Column('trial_credits', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('purchased_credits', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('balance', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_granted', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_consumed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('trial_credits_used', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # Create indexes for credit_accounts
    op.create_index('ix_credit_accounts_merchant_id', 'credit_accounts', ['merchant_id'])
    op.create_index('ix_credit_accounts_platform_domain', 'credit_accounts', ['platform_domain'])
    op.create_index('ix_credit_accounts_platform_name_id', 'credit_accounts', ['platform_name', 'platform_id'])

    # Create unique constraint for merchant_id
    op.create_unique_constraint('uq_credit_accounts_merchant_id', 'credit_accounts', ['merchant_id'])

    # Create credit_transactions table
    op.create_table(
        'credit_transactions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('account_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('merchant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('amount', sa.Integer(), nullable=False),
        sa.Column('operation', sa.String(50), nullable=False),
        sa.Column('source', sa.String(50), nullable=False),
        sa.Column('balance_before', sa.Integer(), nullable=False),
        sa.Column('balance_after', sa.Integer(), nullable=False),
        sa.Column('trial_before', sa.Integer(), nullable=True),
        sa.Column('trial_after', sa.Integer(), nullable=True),
        sa.Column('purchased_before', sa.Integer(), nullable=True),
        sa.Column('purchased_after', sa.Integer(), nullable=True),
        sa.Column('reference_type', sa.String(100), nullable=False),
        sa.Column('reference_id', sa.String(255), nullable=False),
        sa.Column('metadata', postgresql.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
    )

    # Create indexes for credit_transactions
    op.create_index('ix_credit_transactions_merchant_created', 'credit_transactions', ['merchant_id', 'created_at'])

    # Create unique constraint for reference deduplication
    op.create_unique_constraint('uq_credit_transactions_reference', 'credit_transactions', ['reference_type', 'reference_id'])


def downgrade() -> None:
    op.drop_table('credit_transactions')
    op.drop_table('credit_accounts')
