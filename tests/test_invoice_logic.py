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
from backend.models.journal import JournalEntry, JournalEntryLine
from backend.services.invoice_service import post_invoice

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
        rev = Account(name="Sales", code="4000", type="Revenue", subtype="Revenue")
        tax_pay = Account(name="Sales Tax Payable", code="2200", type="Liability", subtype="Current Liability")
        db.session.add_all([ar, rev, tax_pay])
        
        # Create settings
        settings = Settings(business_name="Test Business")
        db.session.add(settings)

        # Create a tax
        gst = Tax(name="GST", rate=Decimal('0.05'))
        db.session.add(gst)
        
        # Create a customer
        customer = Customer(name="Test Customer")
        db.session.add(customer)
        
        db.session.commit()
        yield app
        db.session.rollback()
        db.drop_all()
        db.session.remove()

def test_invoice_calculation(app):
    """
    3.2.1 subtotal calculation
    3.2.2 tax calculation
    3.2.3 Auto-update totals on line changes
    """
    with app.app_context():
        customer = Customer.query.first()
        rev_account = Account.query.filter_by(code="4000").first()
        
        invoice = Invoice(
            customer_id=customer.id,
            invoice_number="INV-001",
            issue_date=date.today(),
            due_date=date.today(),
            status='draft'
        )
        db.session.add(invoice)
        db.session.commit()
        
        assert invoice.subtotal == Decimal('0.00')
        assert invoice.tax == Decimal('0.00')
        assert invoice.total == Decimal('0.00')
        
        # Add a line
        gst = Tax.query.filter_by(name="GST").first()
        line1 = InvoiceLine(
            invoice=invoice,
            description="Item 1",
            quantity=Decimal('2.00'),
            unit_price=Decimal('50.00'),
            account_id=rev_account.id,
            taxes=[gst]
        )
        db.session.add(line1)
        db.session.commit()
        
        # Refresh from DB to see auto-updates
        db.session.refresh(invoice)
        
        assert line1.line_total == Decimal('100.00')
        assert invoice.subtotal == Decimal('100.00')
        assert invoice.tax == Decimal('5.00') # 5% of 100
        assert invoice.total == Decimal('105.00')
        assert invoice.balance == Decimal('105.00')
        
        # Add another line
        line2 = InvoiceLine(
            invoice=invoice,
            description="Item 2",
            quantity=Decimal('1.00'),
            unit_price=Decimal('25.00'),
            account_id=rev_account.id,
            taxes=[gst]
        )
        db.session.add(line2)
        db.session.commit()
        
        db.session.refresh(invoice)
        assert invoice.subtotal == Decimal('125.00')
        assert invoice.tax == Decimal('6.25') # 5% of 125
        assert invoice.total == Decimal('131.25')
        
        # Update a line
        line1.quantity = Decimal('3.00')
        db.session.commit()
        
        db.session.refresh(invoice)
        assert invoice.subtotal == Decimal('175.00') # (3*50) + (1*25) = 150 + 25 = 175
        assert invoice.tax == Decimal('8.75') # 5% of 175
        assert invoice.total == Decimal('183.75')
        
        # Delete a line
        db.session.delete(line2)
        db.session.commit()
        
        db.session.refresh(invoice)
        assert invoice.subtotal == Decimal('150.00')
        assert invoice.tax == Decimal('7.50')
        assert invoice.total == Decimal('157.50')

def test_post_invoice(app):
    """
    3.2.4 Generate journal entry for invoice
    3.2.5 Update customer A/R balance
    """
    with app.app_context():
        customer = Customer.query.first()
        rev_account = Account.query.filter_by(code="4000").first()
        ar_account = Account.query.filter_by(code="1200").first()
        tax_account = Account.query.filter_by(code="2200").first()
        
        invoice = Invoice(
            customer_id=customer.id,
            invoice_number="INV-002",
            issue_date=date.today(),
            due_date=date.today(),
            status='draft'
        )
        db.session.add(invoice)
        db.session.flush()
        
        gst = Tax.query.filter_by(name="GST").first()
        line = InvoiceLine(
            invoice_id=invoice.id,
            description="Service",
            quantity=Decimal('1.00'),
            unit_price=Decimal('100.00'),
            account_id=rev_account.id,
            taxes=[gst]
        )
        db.session.add(line)
        db.session.commit()
        
        # Post the invoice
        posted_invoice = post_invoice(invoice.id)
        
        assert posted_invoice.status == 'sent'
        
        # Check journal entry
        journal_entry = JournalEntry.query.filter_by(reference="INV-INV-002").first()
        assert journal_entry is not None
        assert journal_entry.date == date.today()
        
        # Check lines
        # Total: 105.00 (100 + 5.00 tax)
        # Debit: AR (105.00)
        # Credit: Revenue (100.00)
        # Credit: Tax Payable (5.00)
        
        ar_line = [l for l in journal_entry.lines if l.account_id == ar_account.id][0]
        rev_line = [l for l in journal_entry.lines if l.account_id == rev_account.id][0]
        tax_line = [l for l in journal_entry.lines if l.account_id == tax_account.id][0]
        
        assert ar_line.debit == Decimal('105.00')
        assert ar_line.credit == Decimal('0.00')
        
        assert rev_line.debit == Decimal('0.00')
        assert rev_line.credit == Decimal('100.00')
        
        assert tax_line.debit == Decimal('0.00')
        assert tax_line.credit == Decimal('5.00')
        
        assert journal_entry.is_balanced() is True
        
        # Check customer balance
        db.session.refresh(customer)
        assert customer.balance == Decimal('105.00')

def test_invoice_multiple_taxes(app):
    with app.app_context():
        customer = Customer.query.first()
        rev_account = Account.query.filter_by(code="4000").first()
        
        # Create two taxes
        tax1 = Tax(name="Tax 1", rate=Decimal('0.05'))
        tax2 = Tax(name="Tax 2", rate=Decimal('0.02'))
        db.session.add_all([tax1, tax2])
        db.session.commit()
        
        invoice = Invoice(
            customer_id=customer.id,
            invoice_number="INV-MULTITAX",
            issue_date=date.today(),
            due_date=date.today(),
            status='draft'
        )
        db.session.add(invoice)
        
        line = InvoiceLine(
            invoice=invoice,
            description="Item with 2 taxes",
            quantity=Decimal('1.00'),
            unit_price=Decimal('100.00'),
            account_id=rev_account.id,
            taxes=[tax1, tax2]
        )
        db.session.add(line)
        db.session.commit()
        
        db.session.refresh(invoice)
        assert invoice.subtotal == Decimal('100.00')
        assert invoice.tax == Decimal('7.00') # 5.00 + 2.00
        assert invoice.total == Decimal('107.00')
