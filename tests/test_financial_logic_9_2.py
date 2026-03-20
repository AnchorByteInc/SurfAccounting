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
from backend.models.settings import Settings
from backend.models.tax import Tax
from backend.models.journal import JournalEntry, JournalEntryLine
from backend.services.invoice_service import post_invoice
from backend.services.bill_service import post_bill
from backend.services.payment_service import apply_payment, apply_vendor_payment
from backend.services import report_service
from backend.services.journal_service import save_journal_entry

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
            Account(name="Cash", code="1000", type="Asset", subtype="Bank"),
            Account(name="Accounts Receivable", code="1200", type="Asset", subtype="Accounts Receivable"),
            Account(name="Inventory", code="1400", type="Asset", subtype="Current Asset"),
            Account(name="Accounts Payable", code="2000", type="Liability", subtype="Accounts Payable"),
            Account(name="Sales Tax Payable", code="2200", type="Liability", subtype="Current Liability"),
            Account(name="Owner's Equity", code="3000", type="Equity", subtype="Equity"),
            Account(name="Sales", code="4000", type="Revenue", subtype="Revenue"),
            Account(name="Cost of Goods Sold", code="5000", type="Expense", subtype="Cost of Goods Sold"),
            Account(name="Rent Expense", code="5300", type="Expense", subtype="Operating Expense"),
        ]
        db.session.add_all(accounts)
        
        # Create settings
        settings = Settings(business_name="Test Corp")
        db.session.add(settings)
        
        # Create a tax
        tax = Tax(name="Tax", rate=Decimal('0.10'))
        db.session.add(tax)
        
        # Create customer and vendor
        customer = Customer(name="Test Customer")
        vendor = Vendor(name="Test Vendor")
        db.session.add_all([customer, vendor])
        
        db.session.commit()
        yield app
        db.session.rollback()
        db.drop_all()
        db.session.remove()

def test_9_2_1_double_entry_enforcement(app):
    """9.2.1 Test double-entry enforcement"""
    with app.app_context():
        cash = Account.query.filter_by(code="1000").first()
        equity = Account.query.filter_by(code="3000").first()
        
        # 1. Test is_balanced method
        entry = JournalEntry(date=date.today(), memo="Balanced")
        entry.lines.append(JournalEntryLine(account_id=cash.id, debit=Decimal('100.00')))
        entry.lines.append(JournalEntryLine(account_id=equity.id, credit=Decimal('100.00')))
        assert entry.is_balanced() is True
        
        unbalanced = JournalEntry(date=date.today(), memo="Unbalanced")
        unbalanced.lines.append(JournalEntryLine(account_id=cash.id, debit=Decimal('100.00')))
        unbalanced.lines.append(JournalEntryLine(account_id=equity.id, credit=Decimal('50.00')))
        assert unbalanced.is_balanced() is False
        
        # 2. Test saving unbalanced entry via service
        with pytest.raises(ValueError, match="Journal entry is not balanced"):
            save_journal_entry(unbalanced)
            
        # 3. Test DB level enforcement via event listener
        db.session.add(unbalanced)
        with pytest.raises(ValueError, match="Journal entry is not balanced"):
            db.session.commit()
        db.session.rollback()

def test_9_2_2_invoice_posting_entries(app):
    """9.2.2 Test invoice posting entries"""
    with app.app_context():
        customer = Customer.query.first()
        sales_acc = Account.query.filter_by(code="4000").first()
        ar_acc = Account.query.filter_by(code="1200").first()
        tax_acc = Account.query.filter_by(code="2200").first()
        
        invoice = Invoice(
            customer_id=customer.id,
            invoice_number="INV-922",
            issue_date=date.today(),
            due_date=date.today(),
            status='draft'
        )
        db.session.add(invoice)
        db.session.flush()
        
        line = InvoiceLine(
            invoice_id=invoice.id,
            description="Consulting",
            quantity=Decimal('2.00'),
            unit_price=Decimal('100.00'),
            account_id=sales_acc.id
        )
        line.taxes.append(Tax.query.filter_by(name="Tax").first())
        db.session.add(line)
        db.session.commit()
        
        # Post invoice: Subtotal 200, Tax (10%) 20, Total 220
        post_invoice(invoice.id)
        
        # Check journal entry
        je = JournalEntry.query.filter_by(reference="INV-INV-922").first()
        assert je is not None
        assert je.is_balanced() is True
        
        # Check lines
        # Debit AR: 220
        # Credit Sales: 200
        # Credit Tax: 20
        ar_line = next(line for line in je.lines if line.account_id == ar_acc.id)
        sales_line = next(line for line in je.lines if line.account_id == sales_acc.id)
        tax_line = next(line for line in je.lines if line.account_id == tax_acc.id)
        
        assert ar_line.debit == Decimal('220.00')
        assert sales_line.credit == Decimal('200.00')
        assert tax_line.credit == Decimal('20.00')
        
        # Check customer balance
        db.session.refresh(customer)
        assert customer.balance == Decimal('220.00')

def test_9_2_3_payment_journal_entries(app):
    """9.2.3 Test payment journal entries"""
    with app.app_context():
        customer = Customer.query.first()
        vendor = Vendor.query.first()
        cash_acc = Account.query.filter_by(code="1000").first()
        ar_acc = Account.query.filter_by(code="1200").first()
        ap_acc = Account.query.filter_by(code="2000").first()
        
        # 1. Customer Payment
        invoice = Invoice(
            customer_id=customer.id,
            invoice_number="INV-PAY",
            issue_date=date.today(),
            due_date=date.today(),
            total=Decimal('100.00'),
            balance=Decimal('100.00'),
            status='sent'
        )
        db.session.add(invoice)
        db.session.commit()
        
        # Post-entry for AR (otherwise customer balance would be wrong for this test)
        # In a real flow, post_invoice handles this. Here we manually ensure the customer balance reflects the invoice.
        customer.balance = Decimal('100.00')
        db.session.commit()
        
        payment = apply_payment(
            amount=Decimal('100.00'),
            date_paid=date.today(),
            customer_id=customer.id,
            invoice_id=invoice.id,
            method="Cash"
        )
        
        je_pay = JournalEntry.query.filter_by(reference=f"PAY-{payment.id}").first()
        assert je_pay is not None
        assert je_pay.is_balanced() is True
        
        # Debit Cash: 100, Credit AR: 100
        cash_line = next(line for line in je_pay.lines if line.account_id == cash_acc.id)
        ar_line = next(line for line in je_pay.lines if line.account_id == ar_acc.id)
        assert cash_line.debit == Decimal('100.00')
        assert ar_line.credit == Decimal('100.00')
        
        # 2. Vendor Payment
        bill = Bill(
            vendor_id=vendor.id,
            bill_number="BILL-PAY",
            issue_date=date.today(),
            due_date=date.today(),
            total=Decimal('500.00'),
            balance=Decimal('500.00'),
            status='approved'
        )
        db.session.add(bill)
        db.session.commit()
        
        # Manually set vendor balance for test
        vendor.balance = Decimal('500.00')
        db.session.commit()
        
        vpayment = apply_vendor_payment(
            amount=Decimal('500.00'),
            date_paid=date.today(),
            vendor_id=vendor.id,
            bill_id=bill.id,
            method="Bank Transfer"
        )
        
        je_vpay = JournalEntry.query.filter_by(reference=f"VPAY-{vpayment.id}").first()
        assert je_vpay is not None
        assert je_vpay.is_balanced() is True
        
        # Debit AP: 500, Credit Cash: 500
        ap_line = next(line for line in je_vpay.lines if line.account_id == ap_acc.id)
        cash_line_v = next(line for line in je_vpay.lines if line.account_id == cash_acc.id)
        assert ap_line.debit == Decimal('500.00')
        assert cash_line_v.credit == Decimal('500.00')

def test_9_2_4_balance_sheet_integrity(app):
    """9.2.4 Test balance sheet integrity"""
    with app.app_context():
        customer = Customer.query.first()
        vendor = Vendor.query.first()
        cash_acc = Account.query.filter_by(code="1000").first()
        sales_acc = Account.query.filter_by(code="4000").first()
        rent_acc = Account.query.filter_by(code="5300").first()
        
        # Initial state: everything 0.
        bs = report_service.get_balance_sheet(date.today())
        assert bs['total_assets'] == 0
        assert bs['total_liabilities'] == 0
        assert bs['total_equity'] == 0
        
        # 1. Invest Cash (Capital contribution)
        je = JournalEntry(date=date.today(), memo="Initial Investment")
        je.lines.append(JournalEntryLine(account_id=cash_acc.id, debit=Decimal('10000.00')))
        je.lines.append(JournalEntryLine(account_id=Account.query.filter_by(code="3000").first().id, credit=Decimal('10000.00')))
        db.session.add(je)
        db.session.commit()
        
        bs = report_service.get_balance_sheet(date.today())
        assert bs['total_assets'] == 10000.0
        assert bs['total_liabilities'] == 0.0
        assert bs['total_equity'] == 10000.0
        assert bs['total_assets'] == bs['total_liabilities'] + bs['total_equity']
        
        # 2. Sale on account (Invoice)
        inv = Invoice(customer_id=customer.id, invoice_number="INV-BS", issue_date=date.today(), due_date=date.today())
        db.session.add(inv)
        db.session.flush()
        inv_line = InvoiceLine(invoice_id=inv.id, description="Sales", quantity=1, unit_price=1000, account_id=sales_acc.id)
        inv_line.taxes.append(Tax.query.filter_by(name="Tax").first())
        db.session.add(inv_line)
        db.session.commit()
        post_invoice(inv.id) # Tax rate is 10%, so 1100 total.
        
        # Assets: 10000 (Cash) + 1100 (AR) = 11100
        # Liabilities: 100 (Tax Payable)
        # Equity: 10000 (Initial) + 1000 (Net Income) = 11000
        # 11100 = 100 + 11000. OK.
        
        bs = report_service.get_balance_sheet(date.today())
        assert bs['total_assets'] == 11100.0
        assert bs['total_liabilities'] == 100.0
        assert bs['total_equity'] == 11000.0
        assert bs['total_assets'] == bs['total_liabilities'] + bs['total_equity']
        
        # 3. Rent Bill
        bill = Bill(vendor_id=vendor.id, bill_number="BILL-BS", issue_date=date.today(), due_date=date.today())
        db.session.add(bill)
        db.session.flush()
        db.session.add(BillLine(bill_id=bill.id, description="Rent", quantity=1, unit_cost=500, account_id=rent_acc.id))
        db.session.commit()
        post_bill(bill.id)
        
        # Assets: 11100
        # Liabilities: 100 (Tax) + 500 (AP) = 600
        # Equity: 11000 (Prev) - 500 (Rent expense) = 10500
        # 11100 = 600 + 10500. OK.
        
        bs = report_service.get_balance_sheet(date.today())
        assert bs['total_assets'] == 11100.0
        assert bs['total_liabilities'] == 600.0
        assert bs['total_equity'] == 10500.0
        assert bs['total_assets'] == bs['total_liabilities'] + bs['total_equity']
        
        # 4. Pay Bill
        apply_vendor_payment(amount=Decimal('500.00'), date_paid=date.today(), vendor_id=vendor.id, bill_id=bill.id)
        
        # Assets: 11100 - 500 (Cash) = 10600
        # Liabilities: 600 - 500 (AP) = 100
        # Equity: 10500
        # 10600 = 100 + 10500. OK.
        
        bs = report_service.get_balance_sheet(date.today())
        assert bs['total_assets'] == 10600.0
        assert bs['total_liabilities'] == 100.0
        assert bs['total_equity'] == 10500.0
        assert bs['total_assets'] == bs['total_liabilities'] + bs['total_equity']
        
        # 5. Receive Payment
        apply_payment(amount=Decimal('1100.00'), date_paid=date.today(), customer_id=customer.id, invoice_id=inv.id)
        
        # Assets: 10600 - 1100 (AR) + 1100 (Cash) = 10600
        # Liabilities: 100
        # Equity: 10500
        # 10600 = 100 + 10500. OK.
        
        bs = report_service.get_balance_sheet(date.today())
        assert bs['total_assets'] == 10600.0
        assert bs['total_liabilities'] == 100.0
        assert bs['total_equity'] == 10500.0
        assert bs['total_assets'] == bs['total_liabilities'] + bs['total_equity']
