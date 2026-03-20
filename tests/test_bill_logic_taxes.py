import pytest
from datetime import date
from decimal import Decimal
from backend.app import create_app
from backend.config import Config
from backend.extensions import db
from backend.models.account import Account
from backend.models.vendor import Vendor
from backend.models.bill import Bill, BillLine
from backend.models.tax import Tax
from backend.models.journal import JournalEntry
from backend.services.bill_service import post_bill

class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True

@pytest.fixture
def app():
    app = create_app(TestConfig)
    
    with app.app_context():
        db.create_all()
        # Create some test accounts
        ap = Account(name="Accounts Payable", code="2100", type="Liability", subtype="Accounts Payable")
        expense = Account(name="Office Supplies", code="6000", type="Expense", subtype="Expense")
        db.session.add_all([ap, expense])
        
        # Create a vendor
        vendor = Vendor(name="Test Vendor")
        db.session.add(vendor)
        
        db.session.commit()
        yield app
        db.session.rollback()
        db.drop_all()
        db.session.remove()

def test_bill_multiple_taxes(app):
    with app.app_context():
        vendor = Vendor.query.first()
        expense_account = Account.query.filter_by(code="6000").first()
        
        # Create two taxes
        tax1 = Tax(name="GST 7%", rate=Decimal('0.07'))
        tax2 = Tax(name="VAT 10%", rate=Decimal('0.10'))
        db.session.add_all([tax1, tax2])
        db.session.commit()
        
        bill = Bill(
            vendor_id=vendor.id,
            bill_number="BILL-MULTITAX",
            issue_date=date.today(),
            due_date=date.today(),
            status='draft'
        )
        db.session.add(bill)
        
        line = BillLine(
            bill=bill,
            description="Item with 2 taxes",
            quantity=Decimal('2.00'),
            unit_cost=Decimal('100.00'),
            account_id=expense_account.id,
            taxes=[tax1, tax2]
        )
        db.session.add(line)
        db.session.commit()
        
        db.session.refresh(bill)
        assert bill.subtotal == Decimal('200.00')
        # Tax 1: 200 * 0.07 = 14.00
        # Tax 2: 200 * 0.10 = 20.00
        # Total Tax: 34.00
        assert bill.tax == Decimal('34.00')
        assert bill.total == Decimal('234.00')

def test_post_bill_with_taxes(app):
    with app.app_context():
        # Need to add Sales Tax Payable account
        tax_account = Account(name="Sales Tax Payable", code="2200", type="Liability", subtype="Current Liability")
        db.session.add(tax_account)
        db.session.commit()

        vendor = Vendor.query.first()
        expense_account = Account.query.filter_by(code="6000").first()
        ap_account = Account.query.filter_by(code="2100").first()
        
        tax = Tax(name="VAT 10%", rate=Decimal('0.10'))
        db.session.add(tax)
        db.session.commit()
        
        bill = Bill(
            vendor_id=vendor.id,
            bill_number="BILL-TAX-POST",
            issue_date=date.today(),
            due_date=date.today(),
            status='draft'
        )
        db.session.add(bill)
        
        line = BillLine(
            bill=bill,
            description="Item",
            quantity=Decimal('1.00'),
            unit_cost=Decimal('100.00'),
            account_id=expense_account.id,
            taxes=[tax]
        )
        db.session.add(line)
        db.session.commit()
        
        # Post the bill
        posted_bill = post_bill(bill.id)
        
        assert posted_bill.status == 'approved'
        
        # Check journal entry
        journal_entry = JournalEntry.query.filter_by(reference=f"BILL-{bill.bill_number}").first()
        assert journal_entry is not None
        assert journal_entry.is_balanced() is True
        
        # Credits: AP (110.00)
        # Debits: Expense (110.00) - (100.00 line + 10.00 tax)
        
        ap_lines = [line for line in journal_entry.lines if line.account_id == ap_account.id]
        expense_lines = [line for line in journal_entry.lines if line.account_id == expense_account.id]
        
        assert ap_lines[0].credit == Decimal('110.00')
        assert sum(line.debit for line in expense_lines) == Decimal('110.00')
