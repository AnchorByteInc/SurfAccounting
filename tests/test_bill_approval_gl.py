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
from backend.services.bill_service import post_bill, sync_bill_gl
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
        ap = Account(name="Accounts Payable", code="2000", type="Liability", subtype="Accounts Payable")
        expense = Account(name="Rent", code="5300", type="Expense", subtype="Operating Expense")
        cash = Account(name="Cash", code="1000", type="Asset", subtype="Cash")
        db.session.add_all([ap, expense, cash])
        
        # Create a vendor
        vendor = Vendor(name="Test Vendor")
        db.session.add(vendor)
        
        db.session.commit()
        yield app
        db.session.rollback()
        db.drop_all()
        db.session.remove()

def test_bill_approval_and_gl(app):
    """
    Test that approving a bill creates GL transactions with correct Source Module/ID.
    """
    with app.app_context():
        vendor = Vendor.query.first()
        expense_account = Account.query.filter_by(code="5300").first()
        ap_account = Account.query.filter_by(code="2000").first()
        
        # 1. Create Draft Bill
        bill = Bill(
            vendor_id=vendor.id,
            bill_number="BILL-001",
            issue_date=date.today(),
            due_date=date.today(),
            status='draft'
        )
        db.session.add(bill)
        
        line = BillLine(
            bill=bill,
            description="Office Rent",
            quantity=Decimal('1.00'),
            unit_cost=Decimal('1000.00'),
            account_id=expense_account.id
        )
        db.session.add(line)
        db.session.commit()
        
        # Verify no GL yet
        assert JournalEntry.query.filter_by(source_module="BILL", source_id=bill.id).first() is None
        
        # 2. Approve Bill
        posted_bill = post_bill(bill.id)
        assert posted_bill.status == 'approved'
        
        # Verify GL created
        je = JournalEntry.query.filter_by(source_module="BILL", source_id=bill.id).first()
        assert je is not None
        assert je.transaction_type == "Bill"
        assert je.vendor_id == vendor.id
        assert len(je.lines) == 2
        
        # Check A/P line
        ap_line = [line for line in je.lines if line.account_id == ap_account.id][0]
        assert ap_line.credit == Decimal('1000.00')
        assert ap_line.debit == Decimal('0.00')
        
        # Check Expense line
        exp_line = [line for line in je.lines if line.account_id == expense_account.id][0]
        assert exp_line.debit == Decimal('1000.00')
        assert exp_line.credit == Decimal('0.00')

def test_bill_edit_after_approval(app):
    """
    Test that editing an approved bill corrects the GL transactions.
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
            status='approved'
        )
        db.session.add(bill)
        
        line = BillLine(
            bill=bill,
            description="Office Rent",
            quantity=Decimal('1.00'),
            unit_cost=Decimal('1000.00'),
            account_id=expense_account.id
        )
        db.session.add(line)
        db.session.commit()
        
        # Manually sync GL since we created it as approved
        sync_bill_gl(bill.id)
        db.session.commit()
        
        je = JournalEntry.query.filter_by(source_module="BILL", source_id=bill.id).first()
        assert je is not None
        assert len(je.lines) == 2
        ap_line = [line for line in je.lines if line.account_id == ap_account.id][0]
        assert ap_line.credit == Decimal('1000.00')
        
        # Edit the bill line
        line.unit_cost = Decimal('1200.00')
        # Simulate route behavior by calling sync_bill_gl
        sync_bill_gl(bill.id)
        db.session.commit()
        
        # Verify GL updated
        db.session.refresh(je)
        ap_line = [line for line in je.lines if line.account_id == ap_account.id][0]
        assert ap_line.credit == Decimal('1200.00')
        
        # Add another line
        line2 = BillLine(
            bill=bill,
            description="Utilities",
            quantity=Decimal('1.00'),
            unit_cost=Decimal('200.00'),
            account_id=expense_account.id
        )
        db.session.add(line2)
        sync_bill_gl(bill.id)
        db.session.commit()
        
        # Verify GL updated
        db.session.refresh(je)
        assert len(je.lines) == 3 # 1 AP, 2 Expense
        ap_line = [line for line in je.lines if line.account_id == ap_account.id][0]
        assert ap_line.credit == Decimal('1400.00') # 1200 + 200

def test_bill_payment_clears_ap(app):
    """
    Test that making a payment clears the A/P GL transaction.
    """
    with app.app_context():
        vendor = Vendor.query.first()
        expense_account = Account.query.filter_by(code="5300").first()
        ap_account = Account.query.filter_by(code="2000").first()
        cash_account = Account.query.filter_by(code="1000").first()
        
        # 1. Create and Approve Bill
        bill = Bill(
            vendor_id=vendor.id,
            bill_number="BILL-003",
            issue_date=date.today(),
            due_date=date.today(),
            status='draft'
        )
        db.session.add(bill)
        line = BillLine(bill=bill, quantity=1, unit_cost=1000, account_id=expense_account.id)
        db.session.add(line)
        db.session.commit()
        
        post_bill(bill.id)
        
        je_bill = JournalEntry.query.filter_by(source_module="BILL", source_id=bill.id).first()
        assert je_bill is not None
        
        # 2. Make Payment
        payment = apply_vendor_payment(
            amount=1000,
            date_paid=date.today(),
            vendor_id=vendor.id,
            bill_id=bill.id,
            account_id=cash_account.id
        )
        
        # Verify Payment GL
        je_pay = JournalEntry.query.filter_by(source_module="VPAY", source_id=payment.id).first()
        assert je_pay is not None
        assert je_pay.transaction_type == "Payment"
        
        # Check A/P line in Payment GL (Debit decreases liability)
        ap_pay_line = [line for line in je_pay.lines if line.account_id == ap_account.id][0]
        assert ap_pay_line.debit == Decimal('1000.00')
        assert ap_pay_line.credit == Decimal('0.00')
        
        # Check Cash line in Payment GL (Credit decreases asset)
        cash_pay_line = [line for line in je_pay.lines if line.account_id == cash_account.id][0]
        assert cash_pay_line.credit == Decimal('1000.00')
        assert cash_pay_line.debit == Decimal('0.00')
        
        # Verify Bill Status
        assert bill.status == 'paid'
        assert bill.balance == Decimal('0.00')

def test_bill_revert_to_draft_deletes_gl(app):
    """
    Test that changing an approved bill back to draft deletes its GL transaction.
    """
    with app.app_context():
        vendor = Vendor.query.first()
        expense_account = Account.query.filter_by(code="5300").first()
        
        bill = Bill(
            vendor_id=vendor.id,
            bill_number="BILL-004",
            issue_date=date.today(),
            due_date=date.today(),
            status='approved'
        )
        db.session.add(bill)
        line = BillLine(bill=bill, quantity=1, unit_cost=1000, account_id=expense_account.id)
        db.session.add(line)
        db.session.commit()
        
        sync_bill_gl(bill.id)
        db.session.commit()
        
        assert JournalEntry.query.filter_by(source_module="BILL", source_id=bill.id).count() == 1
        
        # Change back to draft
        bill.status = 'draft'
        sync_bill_gl(bill.id)
        db.session.commit()
        
        # Verify GL deleted
        assert JournalEntry.query.filter_by(source_module="BILL", source_id=bill.id).first() is None

def test_cannot_pay_draft_bill(app):
    """
    Test that a bill must be approved before payment.
    """
    with app.app_context():
        vendor = Vendor.query.first()
        expense_account = Account.query.filter_by(code="5300").first()
        cash_account = Account.query.filter_by(code="1000").first()
        
        bill = Bill(
            vendor_id=vendor.id,
            bill_number="BILL-DRAFT-PAY",
            issue_date=date.today(),
            due_date=date.today(),
            status='draft'
        )
        db.session.add(bill)
        line = BillLine(bill=bill, quantity=1, unit_cost=500, account_id=expense_account.id)
        db.session.add(line)
        db.session.commit()
        
        with pytest.raises(ValueError, match="Bill must be approved before payment."):
            apply_vendor_payment(
                amount=500,
                date_paid=date.today(),
                vendor_id=vendor.id,
                bill_id=bill.id,
                account_id=cash_account.id
            )
