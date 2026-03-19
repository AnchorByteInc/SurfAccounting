
import pytest
from datetime import date
from decimal import Decimal
from backend.app import create_app
from backend.config import Config
from backend.extensions import db
from backend.models.account import Account
from backend.models.customer import Customer
from backend.models.vendor import Vendor
from backend.models.invoice import Invoice, InvoiceLine
from backend.models.bill import Bill, BillLine
from backend.models.journal import JournalEntry, JournalEntryLine
from backend.services.invoice_service import post_invoice
from backend.services.bill_service import post_bill
from backend.services.payment_service import apply_payment, apply_vendor_payment

class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True

@pytest.fixture
def app():
    app = create_app(TestConfig)
    
    with app.app_context():
        db.create_all()
        # Seed accounts
        cash_acc = Account(name='Cash', code='1000', type='Asset', subtype='Cash')
        ar_acc = Account(name='Accounts Receivable', code='1200', type='Asset', subtype='Accounts Receivable')
        ap_acc = Account(name='Accounts Payable', code='2000', type='Liability', subtype='Accounts Payable')
        rev_acc = Account(name='Revenue', code='4000', type='Revenue')
        exp_acc = Account(name='Expense', code='5000', type='Expense')
        
        # Create customer and vendor
        customer = Customer(name='Test Customer')
        vendor = Vendor(name='Test Vendor')
        
        db.session.add_all([cash_acc, ar_acc, ap_acc, rev_acc, exp_acc, customer, vendor])
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()

def test_invoice_posting_metadata(app):
    with app.app_context():
        customer = Customer.query.first()
        rev_acc = Account.query.filter_by(code='4000').first()
        ar_acc = Account.query.filter_by(code='1200').first()
        
        invoice = Invoice(customer_id=customer.id, invoice_number="INV-0001", issue_date=date.today(), due_date=date.today())
        line = InvoiceLine(account_id=rev_acc.id, quantity=1, unit_price=100, description="Test Item")
        invoice.lines.append(line)
        db.session.add(invoice)
        db.session.commit()

        post_invoice(invoice.id)
        
        # Check journal entry
        je = JournalEntry.query.filter_by(source_module='INV', source_id=invoice.id).first()
        assert je is not None
        assert je.transaction_type == "Invoice"
        assert je.customer_id == customer.id
        assert je.vendor_id is None
        
        # Check line descriptions
        ar_line = next(l for l in je.lines if l.account_id == ar_acc.id)
        rev_line = next(l for l in je.lines if l.account_id == rev_acc.id)
        
        assert "Accounts Receivable" in ar_line.description
        assert rev_line.description == "Test Item"

def test_bill_posting_metadata(app):
    with app.app_context():
        vendor = Vendor.query.first()
        exp_acc = Account.query.filter_by(code='5000').first()
        ap_acc = Account.query.filter_by(code='2000').first()
        
        bill = Bill(vendor_id=vendor.id, bill_number="BILL-0001", issue_date=date.today(), due_date=date.today())
        line = BillLine(account_id=exp_acc.id, quantity=1, unit_cost=50, description="Office Supplies")
        bill.lines.append(line)
        db.session.add(bill)
        db.session.commit()

        post_bill(bill.id)
        
        # Check journal entry
        je = JournalEntry.query.filter_by(source_module='BILL', source_id=bill.id).first()
        assert je is not None
        assert je.transaction_type == "Bill"
        assert je.vendor_id == vendor.id
        
        # Check line descriptions
        ap_line = next(l for l in je.lines if l.account_id == ap_acc.id)
        exp_line = next(l for l in je.lines if l.account_id == exp_acc.id)
        
        assert "Accounts Payable" in ap_line.description
        assert exp_line.description == "Office Supplies"

def test_payment_metadata(app):
    with app.app_context():
        customer = Customer.query.first()
        cash_acc = Account.query.filter_by(code='1000').first()
        
        payment = apply_payment(amount=100, date_paid=date.today(), customer_id=customer.id)
        
        # Check journal entry
        je = JournalEntry.query.filter_by(source_module='PAY', source_id=payment.id).first()
        assert je is not None
        assert je.transaction_type == "Payment"
        assert je.customer_id == customer.id
        
        cash_line = next(l for l in je.lines if l.account_id == cash_acc.id)
        assert "Payment" in cash_line.description

def test_vendor_payment_metadata(app):
    with app.app_context():
        vendor = Vendor.query.first()
        ap_acc = Account.query.filter_by(code='2000').first()
        
        vpayment = apply_vendor_payment(amount=50, date_paid=date.today(), vendor_id=vendor.id)
        
        # Check journal entry
        je = JournalEntry.query.filter_by(source_module='VPAY', source_id=vpayment.id).first()
        assert je is not None
        assert je.transaction_type == "Payment"
        assert je.vendor_id == vendor.id
        
        ap_line = next(l for l in je.lines if l.account_id == ap_acc.id)
        assert "Accounts Payable" in ap_line.description

