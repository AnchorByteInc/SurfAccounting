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
from backend.models.settings import Settings
from backend.models.journal import JournalEntry, JournalEntryLine
from backend.services.invoice_service import post_invoice
from backend.services.bill_service import post_bill
from backend.services.payment_service import apply_payment, apply_vendor_payment
from backend.services import report_service

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
        settings = Settings(business_name="E2E Test Corp")
        db.session.add(settings)
        
        # Create a tax
        tax = Tax(name="Tax", rate=Decimal('0.10'))
        db.session.add(tax)
        
        db.session.commit()
        yield app
        db.session.rollback()
        db.drop_all()
        db.session.remove()

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def auth_headers(client):
    response = client.post('/api/auth/login', json={
        "username": "admin",
        "password": "admin123"
    })
    token = response.get_json()['access_token']
    return {"Authorization": f"Bearer {token}"}

def test_9_4_1_full_invoice_lifecycle(app, client, auth_headers):
    """9.4.1 Simulate full invoice lifecycle"""
    with app.app_context():
        # 1. Create Customer via API
        cust_resp = client.post('/api/customers', json={"name": "E2E Customer", "email": "e2e@example.com"}, headers=auth_headers)
        assert cust_resp.status_code == 201
        customer_id = cust_resp.get_json()['id']
        
        tax_id = Tax.query.filter_by(name="Tax").first().id
        
        sales_acc = Account.query.filter_by(code="4000").first()
        ar_acc = Account.query.filter_by(code="1200").first()
        cash_acc = Account.query.filter_by(code="1000").first()
        
        # 2. Create Draft Invoice via API
        inv_data = {
            "customer_id": customer_id,
            "invoice_number": "E2E-INV-001",
            "issue_date": date.today().isoformat(),
            "due_date": (date.today() + timedelta(days=30)).isoformat(),
            "status": "draft",
            "lines": [
                {
                    "description": "Item 1",
                    "quantity": 2,
                    "unit_price": 100,
                    "account_id": sales_acc.id,
                    "tax_ids": [tax_id]
                }
            ]
        }
        inv_resp = client.post('/api/invoices', json=inv_data, headers=auth_headers)
        assert inv_resp.status_code == 201
        invoice_id = inv_resp.get_json()['id']
        
        # Verify invoice is draft and has totals
        inv = db.session.get(Invoice, invoice_id)
        assert inv.status == 'draft'
        assert inv.total == Decimal('220.00') # 200 + 10% tax
        assert inv.balance == Decimal('220.00')
        
        # 3. Post Invoice (Since API lacks post endpoint, we use service)
        # In a real E2E, we might be calling an API that calls this service.
        posted_inv = post_invoice(invoice_id)
        assert posted_inv.status == 'sent'
        
        # Verify journal entry was created
        je = JournalEntry.query.filter_by(reference="INV-E2E-INV-001").first()
        assert je is not None
        
        # 4. Apply Payment (Since API create_payment lacks service call, we use service)
        # Note: If we use the API /api/payments, it won't trigger apply_payment logic currently.
        payment = apply_payment(
            amount=Decimal('220.00'),
            date_paid=date.today(),
            customer_id=customer_id,
            invoice_id=invoice_id,
            method="Cash"
        )
        
        # 5. Verify final state
        db.session.refresh(inv)
        assert inv.status == 'paid'
        assert inv.balance == Decimal('0.00')
        
        customer = db.session.get(Customer, customer_id)
        assert customer.balance == Decimal('0.00')
        
        # Cash should be increased
        cash_balance = db.session.query(db.func.sum(JournalEntryLine.debit - JournalEntryLine.credit)).filter(JournalEntryLine.account_id == cash_acc.id).scalar()
        assert cash_balance == Decimal('220.00')

def test_9_4_2_full_bill_lifecycle(app, client, auth_headers):
    """9.4.2 Simulate full bill lifecycle"""
    with app.app_context():
        # 1. Create Vendor via API
        vendor_resp = client.post('/api/vendors', json={"name": "E2E Vendor"}, headers=auth_headers)
        assert vendor_resp.status_code == 201
        vendor_id = vendor_resp.get_json()['id']
        
        rent_acc = Account.query.filter_by(code="5300").first()
        ap_acc = Account.query.filter_by(code="2000").first()
        cash_acc = Account.query.filter_by(code="1000").first()
        
        # 2. Create Draft Bill via API
        bill_data = {
            "vendor_id": vendor_id,
            "bill_number": "E2E-BILL-001",
            "issue_date": date.today().isoformat(),
            "due_date": (date.today() + timedelta(days=7)).isoformat(),
            "status": "draft",
            "lines": [
                {
                    "description": "Monthly Rent",
                    "quantity": 1,
                    "unit_cost": 500,
                    "account_id": rent_acc.id
                }
            ]
        }
        bill_resp = client.post('/api/bills', json=bill_data, headers=auth_headers)
        assert bill_resp.status_code == 201
        bill_id = bill_resp.get_json()['id']
        
        # Verify bill is draft
        bill = db.session.get(Bill, bill_id)
        assert bill.status == 'draft'
        assert bill.total == Decimal('500.00')
        
        # 3. Post Bill (Using service)
        posted_bill = post_bill(bill_id)
        assert posted_bill.status == 'approved'
        
        # Verify journal entry
        je = JournalEntry.query.filter_by(reference="BILL-E2E-BILL-001").first()
        assert je is not None
        
        # 4. Apply Vendor Payment (Using service)
        vpayment = apply_vendor_payment(
            amount=Decimal('500.00'),
            date_paid=date.today(),
            vendor_id=vendor_id,
            bill_id=bill_id,
            method="Bank Transfer"
        )
        
        # 5. Verify final state
        db.session.refresh(bill)
        assert bill.status == 'paid'
        assert bill.balance == Decimal('0.00')
        
        vendor = db.session.get(Vendor, vendor_id)
        assert vendor.balance == Decimal('0.00')

def test_9_4_3_financial_statements_validation(app):
    """9.4.3 Validate financial statements after transactions"""
    with app.app_context():
        # Setup data manually to ensure we know the expected results
        cash_acc = Account.query.filter_by(code="1000").first()
        ar_acc = Account.query.filter_by(code="1200").first()
        ap_acc = Account.query.filter_by(code="2000").first()
        sales_acc = Account.query.filter_by(code="4000").first()
        rent_acc = Account.query.filter_by(code="5300").first()
        equity_acc = Account.query.filter_by(code="3000").first()
        tax_acc = Account.query.filter_by(code="2200").first()
        
        customer = Customer(name="Statement Customer")
        vendor = Vendor(name="Statement Vendor")
        db.session.add_all([customer, vendor])
        db.session.commit()
        
        # 1. Initial Investment: $10,000 Cash
        je1 = JournalEntry(date=date.today(), memo="Investment", reference="INVEST-1")
        je1.lines.append(JournalEntryLine(account_id=cash_acc.id, debit=Decimal('10000.00')))
        je1.lines.append(JournalEntryLine(account_id=equity_acc.id, credit=Decimal('10000.00')))
        db.session.add(je1)
        db.session.commit()
        
        # 2. Sale: $1,000 + $100 Tax = $1,100 AR
        inv = Invoice(customer_id=customer.id, invoice_number="INV-STAT", issue_date=date.today(), due_date=date.today())
        db.session.add(inv)
        db.session.flush()
        inv_line = InvoiceLine(invoice_id=inv.id, description="Sales", quantity=1, unit_price=1000, account_id=sales_acc.id)
        inv_line.taxes.append(Tax.query.filter_by(name="Tax").first())
        db.session.add(inv_line)
        db.session.commit()
        post_invoice(inv.id)
        
        # 3. Expense: $600 Rent
        bill = Bill(vendor_id=vendor.id, bill_number="BILL-STAT", issue_date=date.today(), due_date=date.today())
        db.session.add(bill)
        db.session.flush()
        db.session.add(BillLine(bill_id=bill.id, description="Rent", quantity=1, unit_cost=600, account_id=rent_acc.id))
        db.session.commit()
        post_bill(bill.id)
        
        # Expected Values:
        # Assets: Cash 10000 + AR 1100 = 11100
        # Liabilities: Tax 100 + AP 600 = 700
        # Revenue: 1000
        # Expense: 600
        # Net Income: 400
        # Equity: Investment 10000 + Net Income 400 = 10400
        # Balance Sheet Check: 11100 = 700 + 10400 (True)
        
        # Check Balance Sheet
        bs = report_service.get_balance_sheet(date.today())
        assert bs['total_assets'] == 11100.0
        assert bs['total_liabilities'] == 700.0
        assert bs['total_equity'] == 10400.0
        
        # Check Income Statement
        is_report = report_service.get_income_statement(date.today().replace(day=1), date.today())
        assert is_report['total_revenue'] == 1000.0
        assert is_report['total_expenses'] == 600.0
        assert is_report['net_income'] == 400.0
        
        # 4. Partial Payment Received: $500
        apply_payment(amount=Decimal('500.00'), date_paid=date.today(), customer_id=customer.id, invoice_id=inv.id)
        
        # Assets: Cash (10000+500) + AR (1100-500) = 10500 + 600 = 11100 (Total Assets Unchanged)
        bs = report_service.get_balance_sheet(date.today())
        assert bs['total_assets'] == 11100.0
        
        # 5. Full Bill Payment: $600
        apply_vendor_payment(amount=Decimal('600.00'), date_paid=date.today(), vendor_id=vendor.id, bill_id=bill.id)
        
        # Assets: Cash (10500-600) + AR 600 = 9900 + 600 = 10500
        # Liabilities: Tax 100 + AP (600-600) = 100
        # Equity: 10400
        # Balance Sheet Check: 10500 = 100 + 10400 (True)
        
        bs = report_service.get_balance_sheet(date.today())
        assert bs['total_assets'] == 10500.0
        assert bs['total_liabilities'] == 100.0
        assert bs['total_equity'] == 10400.0
