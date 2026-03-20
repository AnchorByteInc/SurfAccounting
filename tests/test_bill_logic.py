import pytest
from datetime import date
from decimal import Decimal
from backend.app import create_app
from backend.config import Config
from backend.extensions import db
from backend.models.account import Account
from backend.models.vendor import Vendor
from backend.models.bill import Bill, BillLine
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
        ap = Account(name="Accounts Payable", code="2000", type="Liability", subtype="Accounts Payable")
        expense = Account(name="Rent", code="5300", type="Expense", subtype="Operating Expense")
        db.session.add_all([ap, expense])
        
        # Create a vendor
        vendor = Vendor(name="Test Vendor")
        db.session.add(vendor)
        
        db.session.commit()
        yield app
        db.session.rollback()
        db.drop_all()
        db.session.remove()

def test_bill_calculation(app):
    """
    3.4.1 Calculate bill totals
    """
    with app.app_context():
        vendor = Vendor.query.first()
        expense_account = Account.query.filter_by(code="5300").first()
        
        bill = Bill(
            vendor_id=vendor.id,
            bill_number="BILL-001",
            issue_date=date.today(),
            due_date=date.today(),
            status='draft'
        )
        db.session.add(bill)
        db.session.commit()
        
        assert bill.total == Decimal('0.00')
        assert bill.balance == Decimal('0.00')
        
        # Add a line
        line1 = BillLine(
            bill=bill,
            description="Office Rent",
            quantity=Decimal('1.00'),
            unit_cost=Decimal('1000.00'),
            account_id=expense_account.id
        )
        db.session.add(line1)
        db.session.commit()
        
        # Refresh from DB to see auto-updates
        db.session.refresh(bill)
        
        assert line1.line_total == Decimal('1000.00')
        assert bill.total == Decimal('1000.00')
        assert bill.balance == Decimal('1000.00')
        
        # Add another line
        line2 = BillLine(
            bill=bill,
            description="Utilities",
            quantity=Decimal('1.00'),
            unit_cost=Decimal('200.00'),
            account_id=expense_account.id
        )
        db.session.add(line2)
        db.session.commit()
        
        db.session.refresh(bill)
        assert bill.total == Decimal('1200.00')
        
        # Update a line
        line1.quantity = Decimal('2.00')
        db.session.commit()
        
        db.session.refresh(bill)
        assert bill.total == Decimal('2200.00') # (2*1000) + (1*200) = 2200
        
        # Delete a line
        db.session.delete(line2)
        db.session.commit()
        
        db.session.refresh(bill)
        assert bill.total == Decimal('2000.00')

def test_post_bill(app):
    """
    3.4.2 Generate journal entry for bill
    3.4.3 Update vendor A/P balance
    """
    with app.app_context():
        vendor = Vendor.query.first()
        expense_account = Account.query.filter_by(code="5300").first()
        ap_account = Account.query.filter_by(code="2000").first()
        
        bill = Bill(
            vendor_id=vendor.id,
            bill_number="BILL-002",
            issue_date=date.today(),
            due_date=date.today(),
            status='draft'
        )
        db.session.add(bill)
        db.session.flush()
        
        line = BillLine(
            bill=bill,
            description="Office Rent",
            quantity=Decimal('1.00'),
            unit_cost=Decimal('1000.00'),
            account_id=expense_account.id
        )
        db.session.add(line)
        db.session.commit()
        
        # Post the bill
        posted_bill = post_bill(bill.id)
        
        assert posted_bill.status == 'approved'
        
        # Check journal entry
        journal_entry = JournalEntry.query.filter_by(reference="BILL-BILL-002").first()
        assert journal_entry is not None
        assert journal_entry.date == date.today()
        
        # Check lines
        # Debit: Expense (1000.00)
        # Credit: AP (1000.00)
        
        ap_line = [line for line in journal_entry.lines if line.account_id == ap_account.id][0]
        exp_line = [line for line in journal_entry.lines if line.account_id == expense_account.id][0]
        
        assert ap_line.debit == Decimal('0.00')
        assert ap_line.credit == Decimal('1000.00')
        
        assert exp_line.debit == Decimal('1000.00')
        assert exp_line.credit == Decimal('0.00')
        
        assert journal_entry.is_balanced() is True
        
        # Check vendor balance
        db.session.refresh(vendor)
        assert vendor.balance == Decimal('1000.00')
