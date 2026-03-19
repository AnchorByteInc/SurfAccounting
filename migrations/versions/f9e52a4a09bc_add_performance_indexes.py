"""Add performance indexes

Revision ID: f9e52a4a09bc
Revises: 85e8d1c1b583
Create Date: 2026-02-28 14:34:22.639739

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f9e52a4a09bc'
down_revision = '85e8d1c1b583'
branch_labels = None
depends_on = None


def upgrade():
    # Performance indexes (10.1.7)
    op.create_index('ix_invoices_customer_id', 'invoices', ['customer_id'], unique=False)
    op.create_index('ix_invoices_status', 'invoices', ['status'], unique=False)
    op.create_index('ix_invoices_issue_date', 'invoices', ['issue_date'], unique=False)

    op.create_index('ix_bills_vendor_id', 'bills', ['vendor_id'], unique=False)
    op.create_index('ix_bills_status', 'bills', ['status'], unique=False)
    op.create_index('ix_bills_issue_date', 'bills', ['issue_date'], unique=False)

    op.create_index('ix_journal_entries_date', 'journal_entries', ['date'], unique=False)
    op.create_index('ix_journal_entry_lines_account', 'journal_entry_lines', ['account_id'], unique=False)
    op.create_index('ix_journal_entry_lines_entry', 'journal_entry_lines', ['journal_entry_id'], unique=False)

    op.create_index('ix_payments_customer', 'payments', ['customer_id'], unique=False)
    op.create_index('ix_payments_invoice', 'payments', ['invoice_id'], unique=False)
    op.create_index('ix_payments_date', 'payments', ['date'], unique=False)

    op.create_index('ix_vendor_payments_vendor', 'vendor_payments', ['vendor_id'], unique=False)
    op.create_index('ix_vendor_payments_bill', 'vendor_payments', ['bill_id'], unique=False)
    op.create_index('ix_vendor_payments_date', 'vendor_payments', ['date'], unique=False)

    op.create_index('ix_accounting_periods_closed_range', 'accounting_periods', ['start_date','end_date','is_closed'], unique=False)


def downgrade():
    op.drop_index('ix_accounting_periods_closed_range', table_name='accounting_periods')
    op.drop_index('ix_vendor_payments_date', table_name='vendor_payments')
    op.drop_index('ix_vendor_payments_bill', table_name='vendor_payments')
    op.drop_index('ix_vendor_payments_vendor', table_name='vendor_payments')
    op.drop_index('ix_payments_date', table_name='payments')
    op.drop_index('ix_payments_invoice', table_name='payments')
    op.drop_index('ix_payments_customer', table_name='payments')
    op.drop_index('ix_journal_entry_lines_entry', table_name='journal_entry_lines')
    op.drop_index('ix_journal_entry_lines_account', table_name='journal_entry_lines')
    op.drop_index('ix_journal_entries_date', table_name='journal_entries')
    op.drop_index('ix_bills_issue_date', table_name='bills')
    op.drop_index('ix_bills_status', table_name='bills')
    op.drop_index('ix_bills_vendor_id', table_name='bills')
    op.drop_index('ix_invoices_issue_date', table_name='invoices')
    op.drop_index('ix_invoices_status', table_name='invoices')
    op.drop_index('ix_invoices_customer_id', table_name='invoices')
