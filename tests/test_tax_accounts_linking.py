import pytest
from datetime import date, timedelta
from decimal import Decimal
from backend.app import create_app
from backend.config import Config
from backend.extensions import db
from backend.models.account import Account
from backend.models.customer import Customer
from backend.models.vendor import Vendor
from backend.models.invoice import Invoice, InvoiceLine
from backend.models.bill import Bill, BillLine
from backend.models.tax import Tax
from backend.models.journal import JournalEntry, JournalEntryLine
from backend.services.invoice_service import post_invoice
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
        # Create a standard chart of accounts
        accounts = [
            Account(name="Accounts Receivable", code="1200", type="Asset", subtype="Accounts Receivable"),
            Account(name="Accounts Payable", code="2000", type="Liability", subtype="Accounts Payable"),
            Account(name="Sales Tax Payable (Default)", code="2200", type="Liability", subtype="Current Liability"),
            Account(name="Recoverable Tax (Asset)", code="1500", type="Asset", subtype="Current Asset"),
            Account(name="Sales Tax (Liability)", code="2210", type="Liability", subtype="Current Liability"),
            Account(name="Sales", code="4000", type="Revenue", subtype="Revenue"),
            Account(name="Expense", code="5000", type="Expense", subtype="Operating Expense"),
        ]
        db.session.add_all(accounts)
        db.session.commit()
        yield app
        db.session.remove()
        db.drop_all()

def test_tax_account_linking(app):
    with app.app_context():
        # Setup
        asset_tax_acc = Account.query.filter_by(code="1500").first()
        liability_tax_acc = Account.query.filter_by(code="2210").first()
        default_tax_acc = Account.query.filter_by(code="2200").first()
        expense_acc = Account.query.filter_by(code="5000").first()
        sales_acc = Account.query.filter_by(code="4000").first()
        ap_acc = Account.query.filter_by(code="2000").first()
        ar_acc = Account.query.filter_by(code="1200").first()

        # Create Tax with linked accounts
        tax = Tax(
            name="VAT 10%", 
            rate=Decimal('0.10'),
            asset_account_id=asset_tax_acc.id,
            liability_account_id=liability_tax_acc.id
        )
        db.session.add(tax)
        
        # Create Tax without linked accounts (for fallback test)
        default_tax = Tax(
            name="Default Tax 5%",
            rate=Decimal('0.05')
        )
        db.session.add(default_tax)
        
        vendor = Vendor(name="Test Vendor")
        db.session.add(vendor)
        
        customer = Customer(name="Test Customer")
        db.session.add(customer)
        
        db.session.commit()

        # 1. Test Billing (Asset account should be used)
        bill = Bill(
            vendor_id=vendor.id,
            bill_number="BILL-001",
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            status='draft'
        )
        bill_line = BillLine(
            description="Bill Line",
            quantity=Decimal('1.00'),
            unit_cost=Decimal('100.00'),
            account_id=expense_acc.id
        )
        bill_line.taxes.append(tax)
        bill.lines.append(bill_line)
        db.session.add(bill)
        db.session.commit()
        
        # Post bill to trigger GL sync
        post_bill(bill.id)
        
        # Check journal entry for bill
        je_bill = JournalEntry.query.filter_by(source_module="BILL", source_id=bill.id).first()
        assert je_bill is not None
        
        # Look for the tax line
        tax_line = next((l for l in je_bill.lines if l.account_id == asset_tax_acc.id), None)
        assert tax_line is not None
        assert tax_line.debit == Decimal('10.00')
        assert tax_line.credit == Decimal('0.00')
        
        # 2. Test Invoicing (Liability account should be used)
        invoice = Invoice(
            customer_id=customer.id,
            invoice_number="INV-001",
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            status='draft'
        )
        inv_line = InvoiceLine(
            description="Inv Line",
            quantity=Decimal('1.00'),
            unit_price=Decimal('100.00'),
            account_id=sales_acc.id
        )
        inv_line.taxes.append(tax)
        invoice.lines.append(inv_line)
        db.session.add(invoice)
        db.session.commit()
        
        # Post invoice to trigger GL sync
        post_invoice(invoice.id)
        
        # Check journal entry for invoice
        je_inv = JournalEntry.query.filter_by(source_module="INV", source_id=invoice.id).first()
        assert je_inv is not None
        
        # Look for the tax line
        tax_line_inv = next((l for l in je_inv.lines if l.account_id == liability_tax_acc.id), None)
        assert tax_line_inv is not None
        assert tax_line_inv.credit == Decimal('10.00')
        assert tax_line_inv.debit == Decimal('0.00')

        # 3. Test Fallback (Default tax account should be used)
        bill2 = Bill(
            vendor_id=vendor.id,
            bill_number="BILL-002",
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            status='draft'
        )
        bill_line2 = BillLine(
            description="Bill Line 2",
            quantity=Decimal('1.00'),
            unit_cost=Decimal('100.00'),
            account_id=expense_acc.id
        )
        bill_line2.taxes.append(default_tax)
        bill2.lines.append(bill_line2)
        db.session.add(bill2)
        db.session.commit()
        post_bill(bill2.id)
        
        je_bill2 = JournalEntry.query.filter_by(source_module="BILL", source_id=bill2.id).first()
        tax_line2 = next((l for l in je_bill2.lines if l.account_id == default_tax_acc.id), None)
        assert tax_line2 is not None
        assert tax_line2.debit == Decimal('5.00')
