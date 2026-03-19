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
from backend.models.settings import Settings
from backend.services.invoice_service import post_invoice
from backend.services.bill_service import post_bill
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
        # Create some test accounts
        cash = Account(name="Cash", code="1000", type="Asset", subtype="Bank")
        ar = Account(name="Accounts Receivable", code="1200", type="Asset", subtype="Accounts Receivable")
        ap = Account(name="Accounts Payable", code="2000", type="Liability", subtype="Accounts Payable")
        rev = Account(name="Sales", code="4000", type="Revenue", subtype="Revenue")
        exp = Account(name="Rent", code="5300", type="Expense", subtype="Operating Expense")
        tax_pay = Account(name="Sales Tax Payable", code="2200", type="Liability", subtype="Current Liability")
        
        db.session.add_all([cash, ar, ap, rev, exp, tax_pay])
        
        # Create settings
        settings = Settings(business_name="Test Business")
        db.session.add(settings)
        
        # Create a customer and vendor
        customer = Customer(name="Test Customer")
        vendor = Vendor(name="Test Vendor")
        db.session.add_all([customer, vendor])
        
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
    # Get token from auth.login
    response = client.post('/api/auth/login', json={
        "username": "admin",
        "password": "admin123"
    })
    token = response.get_json()['access_token']
    return {"Authorization": f"Bearer {token}"}

def test_income_statement(app):
    with app.app_context():
        customer = Customer.query.first()
        rev_account = Account.query.filter_by(code="4000").first()
        exp_account = Account.query.filter_by(code="5300").first()
        
        # Create an invoice (Revenue)
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
            description="Sale",
            quantity=Decimal('1.00'),
            unit_price=Decimal('100.00'),
            account_id=rev_account.id
        )
        db.session.add(line)
        db.session.commit()
        post_invoice(invoice.id)
        
        # Create a bill (Expense)
        vendor = Vendor.query.first()
        bill = Bill(
            vendor_id=vendor.id,
            bill_number="BILL-001",
            issue_date=date.today(),
            due_date=date.today(),
            status='draft'
        )
        db.session.add(bill)
        db.session.flush()
        bline = BillLine(
            bill_id=bill.id,
            description="Rent",
            quantity=Decimal('1.00'),
            unit_cost=Decimal('40.00'),
            account_id=exp_account.id
        )
        db.session.add(bline)
        db.session.commit()
        post_bill(bill.id)
        
        # Calculate income statement
        start_date = date.today() - timedelta(days=1)
        end_date = date.today() + timedelta(days=1)
        report = report_service.get_income_statement(start_date, end_date)
        
        assert report['total_revenue'] == 100.0
        assert report['total_expenses'] == 40.0
        assert report['net_income'] == 60.0

def test_balance_sheet(app):
    with app.app_context():
        customer = Customer.query.first()
        rev_account = Account.query.filter_by(code="4000").first()
        
        # Create an invoice
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
            description="Sale",
            quantity=Decimal('1.00'),
            unit_price=Decimal('100.00'),
            account_id=rev_account.id
        )
        db.session.add(line)
        db.session.commit()
        post_invoice(invoice.id)
        
        # Balance Sheet as of today
        report = report_service.get_balance_sheet(date.today())
        
        # Assets: AR (100)
        # Liabilities: 0
        # Equity: Net Income (100)
        
        assert report['total_assets'] == 100.0
        assert report['total_liabilities'] == 0.0
        assert report['total_equity'] == 100.0
        
        # Verify it balances: Assets = Liabilities + Equity
        assert report['total_assets'] == report['total_liabilities'] + report['total_equity']

def test_aging_reports(app):
    with app.app_context():
        customer = Customer.query.first()
        rev_account = Account.query.filter_by(code="4000").first()
        
        rev_account = Account.query.filter_by(code="4000").first()
        # Current invoice
        inv1 = Invoice(
            customer_id=customer.id,
            invoice_number="INV-CUR",
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=5),
            status='sent'
        )
        db.session.add(inv1)
        db.session.flush()
        line1 = InvoiceLine(
            invoice_id=inv1.id,
            description="Item 1",
            quantity=Decimal('1.00'),
            unit_price=Decimal('100.00'),
            account_id=rev_account.id
        )
        db.session.add(line1)
        
        # 31-60 days overdue invoice
        inv2 = Invoice(
            customer_id=customer.id,
            invoice_number="INV-OLD",
            issue_date=date.today() - timedelta(days=45),
            due_date=date.today() - timedelta(days=40),
            status='sent'
        )
        db.session.add(inv2)
        db.session.flush()
        line2 = InvoiceLine(
            invoice_id=inv2.id,
            description="Item 2",
            quantity=Decimal('1.00'),
            unit_price=Decimal('200.00'),
            account_id=rev_account.id
        )
        db.session.add(line2)
        
        db.session.commit()
        
        report = report_service.get_ar_aging(date.today())
        
        assert report['summary']['current'] == 100.0
        assert report['summary']['31-60'] == 200.0
        assert report['summary']['total'] == 300.0

        # AP Aging
        vendor = Vendor.query.first()
        exp_account = Account.query.filter_by(code="5300").first()
        bill1 = Bill(
            vendor_id=vendor.id,
            bill_number="BILL-CUR",
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=5),
            status='paid',
            balance=Decimal('0.00'),
            total=Decimal('150.00')
        )
        
        bill2 = Bill(
            vendor_id=vendor.id,
            bill_number="BILL-OLD",
            issue_date=date.today() - timedelta(days=101),
            due_date=date.today() - timedelta(days=91),
            status='draft'
        )
        db.session.add_all([bill1, bill2])
        db.session.flush()

        line2 = BillLine(
            bill=bill2,
            description="Old rent",
            quantity=Decimal('1.00'),
            unit_cost=Decimal('500.00'),
            account_id=exp_account.id
        )
        db.session.add(line2)
        db.session.commit()
        
        ap_report = report_service.get_ap_aging(date.today())
        
        assert ap_report['summary']['90+'] == 500.0
        assert ap_report['summary']['total'] == 500.0
        assert ap_report['summary']['current'] == 0.0

def test_reports_api(client, auth_headers, app):
    with app.app_context():
        customer = Customer.query.first()
        rev_account = Account.query.filter_by(code="4000").first()
        
        # Create an invoice
        invoice = Invoice(
            customer_id=customer.id,
            invoice_number="INV-API",
            issue_date=date.today(),
            due_date=date.today(),
            status='draft'
        )
        db.session.add(invoice)
        db.session.flush()
        line = InvoiceLine(
            invoice_id=invoice.id,
            description="Sale",
            quantity=Decimal('1.00'),
            unit_price=Decimal('100.00'),
            account_id=rev_account.id
        )
        db.session.add(line)
        db.session.commit()
        post_invoice(invoice.id)

    # Test Income Statement API
    start_date = (date.today() - timedelta(days=1)).isoformat()
    end_date = (date.today() + timedelta(days=1)).isoformat()
    response = client.get(f'/api/reports/income-statement?start_date={start_date}&end_date={end_date}', headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()['total_revenue'] == 100.0

    # Test Balance Sheet API
    as_of_date = date.today().isoformat()
    response = client.get(f'/api/reports/balance-sheet?as_of_date={as_of_date}', headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()['total_assets'] == 100.0

    # Test AR Aging API
    response = client.get(f'/api/reports/ar-aging?as_of_date={as_of_date}', headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()['summary']['current'] == 100.0

    # Test Cash Flow API
    response = client.get(f'/api/reports/cash-flow?start_date={start_date}&end_date={end_date}', headers=auth_headers)
    assert response.status_code == 200
    # Starting cash was 0, net income was 100, increase in AR was 100.
    # Net operating cash = 100 (net income) - 100 (AR increase) = 0.
    # Ending cash = 0.
    assert response.get_json()['ending_cash'] == 0.0
