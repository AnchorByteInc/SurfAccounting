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
from backend.services.payment_service import apply_vendor_payment

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
        cash = Account(name="Cash", code="1000", type="Asset", subtype="Cash")
        ap = Account(name="Accounts Payable", code="2000", type="Liability", subtype="Accounts Payable")
        expense = Account(name="Rent", code="5300", type="Expense", subtype="Operating Expense")
        db.session.add_all([cash, ap, expense])
        
        # Create a vendor
        vendor = Vendor(name="Test Vendor")
        db.session.add(vendor)
        
        db.session.commit()
        yield app
        db.session.rollback()
        db.drop_all()
        db.session.remove()

def test_apply_vendor_payment_full(app):
    """
    3.5.1 Apply vendor payment
    3.5.2 Generate journal entry (Debit A/P, Credit Cash)
    """
    with app.app_context():
        vendor = Vendor.query.first()
        expense_account = Account.query.filter_by(code="5300").first()
        ap_account = Account.query.filter_by(code="2000").first()
        cash_account = Account.query.filter_by(code="1000").first()
        
        bill = Bill(
            vendor_id=vendor.id,
            bill_number="BILL-001",
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
        post_bill(bill.id)
        assert bill.balance == Decimal('1000.00')
        assert vendor.balance == Decimal('1000.00')
        
        # Apply full payment
        payment_date = date.today()
        payment = apply_vendor_payment(
            amount=Decimal('1000.00'),
            date_paid=payment_date,
            vendor_id=vendor.id,
            bill_id=bill.id,
            method='Bank Transfer'
        )
        
        db.session.refresh(bill)
        assert payment.amount == Decimal('1000.00')
        assert bill.balance == Decimal('0.00')
        assert bill.status == 'paid'
        
        # Check journal entry
        journal_entry = JournalEntry.query.filter_by(reference=f"VPAY-{payment.id}").first()
        assert journal_entry is not None
        
        # Debit: AP (1000.00)
        # Credit: Cash (1000.00)
        ap_line = [line for line in journal_entry.lines if line.account_id == ap_account.id][0]
        cash_line = [line for line in journal_entry.lines if line.account_id == cash_account.id][0]
        
        assert ap_line.debit == Decimal('1000.00')
        assert ap_line.credit == Decimal('0.00')
        
        assert cash_line.debit == Decimal('0.00')
        assert cash_line.credit == Decimal('1000.00')
        
        # Check vendor balance
        db.session.refresh(vendor)
        assert vendor.balance == Decimal('0.00')

def test_apply_vendor_payment_partial(app):
    """
    3.5.3 Handle partial bill payments
    """
    with app.app_context():
        vendor = Vendor.query.first()
        expense_account = Account.query.filter_by(code="5300").first()
        
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
        
        post_bill(bill.id)
        
        # Apply partial payment
        apply_vendor_payment(
            amount=Decimal('400.00'),
            date_paid=date.today(),
            vendor_id=vendor.id,
            bill_id=bill.id
        )
        
        db.session.refresh(bill)
        assert bill.balance == Decimal('600.00')
        assert bill.status == 'approved'
        
        db.session.refresh(vendor)
        assert vendor.balance == Decimal('600.00')
        
        # Apply another partial payment
        apply_vendor_payment(
            amount=Decimal('600.00'),
            date_paid=date.today(),
            vendor_id=vendor.id,
            bill_id=bill.id
        )
        
        db.session.refresh(bill)
        assert bill.balance == Decimal('0.00')
        assert bill.status == 'paid'
        
        db.session.refresh(vendor)
        assert vendor.balance == Decimal('0.00')
