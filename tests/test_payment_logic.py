import pytest
from datetime import date
from decimal import Decimal
from backend.app import create_app
from backend.config import Config
from backend.extensions import db
from backend.models.account import Account
from backend.models.customer import Customer
from backend.models.invoice import Invoice, InvoiceLine
from backend.models.tax import Tax
from backend.models.settings import Settings
from backend.models.journal import JournalEntry
from backend.services.invoice_service import post_invoice
from backend.services.payment_service import apply_payment

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
        ar = Account(name="Accounts Receivable", code="1200", type="Asset", subtype="Accounts Receivable")
        cash = Account(name="Cash", code="1000", type="Asset", subtype="Bank")
        rev = Account(name="Sales", code="4000", type="Revenue", subtype="Revenue")
        tax_pay = Account(name="Sales Tax Payable", code="2200", type="Liability", subtype="Current Liability")
        db.session.add_all([ar, cash, rev, tax_pay])
        
        # Create settings
        settings = Settings(business_name="Test Business")
        db.session.add(settings)
        
        # Create a tax
        tax = Tax(name="Tax", rate=Decimal('0.05'))
        db.session.add(tax)
        
        # Create a customer
        customer = Customer(name="Test Customer")
        db.session.add(customer)
        
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()

def test_full_payment(app):
    """
    3.3.1 Apply payment to invoice
    3.3.2 Update invoice balance
    3.3.3 Generate journal entry
    """
    with app.app_context():
        customer = Customer.query.first()
        rev_account = Account.query.filter_by(code="4000").first()
        
        # 1. Create and post an invoice
        invoice = Invoice(
            customer_id=customer.id,
            invoice_number="INV-001",
            issue_date=date.today(),
            due_date=date.today(),
            status='draft'
        )
        db.session.add(invoice)
        db.session.flush()
        
        line = InvoiceLine(
            invoice_id=invoice.id,
            description="Service",
            quantity=Decimal('1.00'),
            unit_price=Decimal('100.00'),
            account_id=rev_account.id
        )
        line.taxes.append(Tax.query.filter_by(name="Tax").first())
        db.session.add(line)
        db.session.commit()
        
        post_invoice(invoice.id)
        db.session.refresh(invoice)
        
        assert invoice.total == Decimal('105.00')
        assert invoice.balance == Decimal('105.00')
        assert invoice.status == 'approved'
        
        # 2. Apply full payment
        payment = apply_payment(
            amount=Decimal('105.00'),
            date_paid=date.today(),
            customer_id=customer.id,
            invoice_id=invoice.id,
            method='Bank Transfer'
        )
        
        db.session.refresh(invoice)
        assert invoice.balance == Decimal('0.00')
        assert invoice.status == 'paid'
        
        # 3. Check journal entry
        # Should have PAY-X reference
        journal_entry = JournalEntry.query.filter_by(reference=f"PAY-{payment.id}").first()
        assert journal_entry is not None
        
        cash_account = Account.query.filter_by(code="1000").first()
        ar_account = Account.query.filter_by(code="1200").first()
        
        cash_line = [line for line in journal_entry.lines if line.account_id == cash_account.id][0]
        ar_line = [line for line in journal_entry.lines if line.account_id == ar_account.id][0]
        
        assert cash_line.debit == Decimal('105.00')
        assert ar_line.credit == Decimal('105.00')
        
        # 4. Check customer balance
        db.session.refresh(customer)
        assert customer.balance == Decimal('0.00')

def test_partial_payment(app):
    """
    3.3.4 Handle partial payments
    """
    with app.app_context():
        customer = Customer.query.first()
        rev_account = Account.query.filter_by(code="4000").first()
        
        # 1. Create and post an invoice
        invoice = Invoice(
            customer_id=customer.id,
            invoice_number="INV-002",
            issue_date=date.today(),
            due_date=date.today(),
            status='draft'
        )
        db.session.add(invoice)
        db.session.flush()
        
        line = InvoiceLine(
            invoice_id=invoice.id,
            description="Service",
            quantity=Decimal('1.00'),
            unit_price=Decimal('100.00'),
            account_id=rev_account.id
        )
        line.taxes.append(Tax.query.filter_by(name="Tax").first())
        db.session.add(line)
        db.session.commit()
        
        post_invoice(invoice.id)
        db.session.refresh(invoice)
        
        assert invoice.total == Decimal('105.00')
        
        # 2. Apply partial payment
        apply_payment(
            amount=Decimal('50.00'),
            date_paid=date.today(),
            customer_id=customer.id,
            invoice_id=invoice.id,
            method='Cash'
        )
        
        db.session.refresh(invoice)
        assert invoice.balance == Decimal('55.00')
        assert invoice.status == 'approved' # Should not be paid
        
        db.session.refresh(customer)
        assert customer.balance == Decimal('55.00')
        
        # 3. Apply second partial payment
        apply_payment(
            amount=Decimal('55.00'),
            date_paid=date.today(),
            customer_id=customer.id,
            invoice_id=invoice.id,
            method='Cash'
        )
        
        db.session.refresh(invoice)
        assert invoice.balance == Decimal('0.00')
        assert invoice.status == 'paid'
        
        db.session.refresh(customer)
        assert customer.balance == Decimal('0.00')
