import pytest
from datetime import date
from decimal import Decimal
from backend.app import create_app
from backend.config import Config
from backend.extensions import db
from backend.models.account import Account
from backend.models.customer import Customer
from backend.models.invoice import Invoice, InvoiceLine
from backend.models.journal import JournalEntry

class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        # Setup required accounts
        db.session.add(Account(name="Accounts Receivable", code="1200", type="Asset", subtype="Accounts Receivable"))
        db.session.add(Account(name="Sales", code="4000", type="Revenue", subtype="Revenue"))
        db.session.add(Account(name="Sales Tax Payable", code="2200", type="Liability", subtype="Current Liability"))
        db.session.add(Account(name="Cash", code="1000", type="Asset", subtype="Bank"))
        
        customer = Customer(name="Test Customer")
        db.session.add(customer)
        db.session.commit()
        yield app
        db.session.rollback()
        db.drop_all()

def test_invoice_approval_and_edit_gl_sync(app):
    with app.app_context():
        customer = Customer.query.first()
        rev_acc = Account.query.filter_by(code="4000").first()
        
        # 1. Create a draft invoice
        invoice = Invoice(
            customer_id=customer.id,
            invoice_number="INV-REPRO",
            issue_date=date.today(),
            due_date=date.today(),
            status='draft'
        )
        db.session.add(invoice)
        line = InvoiceLine(
            invoice=invoice,
            description="Test Item",
            quantity=Decimal('1.00'),
            unit_price=Decimal('100.00'),
            account_id=rev_acc.id
        )
        db.session.add(line)
        db.session.commit()
        
        # Verify no GL transaction yet
        journal = JournalEntry.query.filter_by(source_module="INV", source_id=invoice.id).first()
        assert journal is None
        
        # 2. Approve the invoice (change status to 'approved')
        # In the real app, this might happen via POST /invoices/<id>/post
        invoice.status = 'approved'
        db.session.commit()
        
        # Verify GL transaction created
        journal = JournalEntry.query.filter_by(source_module="INV", source_id=invoice.id).first()
        # THIS IS EXPECTED TO PASS NOW
        assert journal is not None, "Journal Entry should be created when invoice is approved"
        total_debits = sum(line.debit for line in journal.lines)
        assert total_debits == Decimal('100.00')
        
        # 3. Edit the invoice after approval
        line.unit_price = Decimal('150.00')
        db.session.commit()
        
        # Verify GL transaction updated
        db.session.refresh(journal)
        total_debits = sum(line.debit for line in journal.lines)
        assert total_debits == Decimal('150.00'), "Journal Entry should be updated when invoice is edited"

def test_payment_gl_sync(app):
    with app.app_context():
        customer = Customer.query.first()
        rev_acc = Account.query.filter_by(code="4000").first()
        ar_acc = Account.query.filter_by(code="1200").first()
        cash_acc = Account.query.filter_by(code="1000").first()
        
        # Setup an invoice with lines to avoid tax=None issues
        invoice = Invoice(
            customer_id=customer.id,
            invoice_number="INV-PAYTEST",
            issue_date=date.today(),
            due_date=date.today(),
            status='approved'
        )
        db.session.add(invoice)
        line = InvoiceLine(
            invoice=invoice,
            description="Test Item",
            quantity=Decimal('1.00'),
            unit_price=Decimal('100.00'),
            account_id=rev_acc.id
        )
        db.session.add(line)
        db.session.commit()
        
        # Record a payment
        # In the real app, this happens via POST /payments which calls apply_payment
        from backend.services.payment_service import apply_payment
        payment = apply_payment(
            amount=Decimal('100.00'),
            date_paid=date.today(),
            customer_id=customer.id,
            invoice_id=invoice.id,
            method='Cash'
        )
        
        # Verify Payment GL transaction
        journal = JournalEntry.query.filter_by(source_module="PAY", source_id=payment.id).first()
        assert journal is not None
        
        # Check lines
        cash_line = [line for line in journal.lines if line.account_id == cash_acc.id][0]
        ar_line = [line for line in journal.lines if line.account_id == ar_acc.id][0]
        
        assert cash_line.debit == Decimal('100.00')
        assert ar_line.credit == Decimal('100.00')

def test_invoice_cancellation(app):
    with app.app_context():
        customer = Customer.query.first()
        rev_acc = Account.query.filter_by(code="4000").first()
        
        # 1. Create a draft invoice
        invoice = Invoice(
            customer_id=customer.id,
            invoice_number="INV-CANCEL",
            issue_date=date.today(),
            due_date=date.today(),
            status='draft'
        )
        db.session.add(invoice)
        line = InvoiceLine(
            invoice=invoice,
            description="Test Item",
            quantity=Decimal('1.00'),
            unit_price=Decimal('100.00'),
            account_id=rev_acc.id
        )
        db.session.add(line)
        db.session.commit()
        
        # Approve it
        invoice.status = 'approved'
        db.session.commit()
        
        # Verify GL transaction exists
        journal = JournalEntry.query.filter_by(source_module="INV", source_id=invoice.id).first()
        assert journal is not None
        
        # 2. Cancel the invoice
        invoice.status = 'cancelled'
        db.session.commit()
        
        # Verify GL transaction deleted
        journal = JournalEntry.query.filter_by(source_module="INV", source_id=invoice.id).first()
        assert journal is None

def test_invoice_deletion(app):
    with app.app_context():
        customer = Customer.query.first()
        rev_acc = Account.query.filter_by(code="4000").first()
        
        # 1. Create a draft invoice
        invoice = Invoice(
            customer_id=customer.id,
            invoice_number="INV-DELETE",
            issue_date=date.today(),
            due_date=date.today(),
            status='draft'
        )
        db.session.add(invoice)
        line = InvoiceLine(
            invoice=invoice,
            description="Test Item",
            quantity=Decimal('1.00'),
            unit_price=Decimal('100.00'),
            account_id=rev_acc.id
        )
        db.session.add(line)
        db.session.commit()
        
        # Approve it
        invoice.status = 'approved'
        db.session.commit()
        
        invoice_id = invoice.id
        # Verify GL transaction exists
        journal = JournalEntry.query.filter_by(source_module="INV", source_id=invoice_id).first()
        assert journal is not None
        
        # 2. Delete the invoice
        db.session.delete(invoice)
        db.session.commit()
        
        # Verify GL transaction deleted
        journal = JournalEntry.query.filter_by(source_module="INV", source_id=invoice_id).first()
        # NOTE: currently this depends on the before_flush which skips deleted instances
        # But wait, session.deleted is checked in before_flush in backend/models/invoice.py
        # and it doesn't call sync_invoice_journal for deleted invoices.
        # I should probably handle deletion too.
        assert journal is None

def test_invoice_created_as_approved(app):
    with app.app_context():
        customer = Customer.query.first()
        rev_acc = Account.query.filter_by(code="4000").first()
        
        # 1. Create an invoice directly as 'sent'
        invoice = Invoice(
            customer_id=customer.id,
            invoice_number="INV-DIRECT",
            issue_date=date.today(),
            due_date=date.today(),
            status='approved'
        )
        db.session.add(invoice)
        line = InvoiceLine(
            invoice=invoice,
            description="Test Item",
            quantity=Decimal('1.00'),
            unit_price=Decimal('100.00'),
            account_id=rev_acc.id
        )
        db.session.add(line)
        db.session.commit()
        
        # Verify GL transaction exists and HAS the source_id
        journal = JournalEntry.query.filter_by(source_module="INV", source_id=invoice.id).first()
        assert journal is not None, "Journal Entry should be created even if invoice is created as sent"
        assert journal.source_id == invoice.id
