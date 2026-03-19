import pytest
from backend.app import create_app
from backend.config import Config
from backend.extensions import db
from backend.models.invoice import Invoice, InvoiceLine
from backend.models.bill import Bill, BillLine
from backend.models.account import Account
from backend.models.journal import JournalEntry, JournalEntryLine
from backend.models.customer import Customer
from backend.models.vendor import Vendor
from datetime import date
from decimal import Decimal

class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.session.rollback()
        db.drop_all()

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

def test_dashboard_data(client, auth_headers, app):
    with app.app_context():
        # 1. Create data for metrics
        
        # Create an Asset account (Bank)
        bank_account = Account(name="Bank", code="1000", type="Asset", subtype="Bank")
        db.session.add(bank_account)
        db.session.commit()
        
        # Add some cash balance
        je = JournalEntry(date=date.today(), memo="Initial balance")
        db.session.add(je)
        db.session.flush()
        jel = JournalEntryLine(journal_entry_id=je.id, account_id=bank_account.id, debit=Decimal('5000.00'), credit=Decimal('0.00'))
        db.session.add(jel)
        # Balanced with Equity
        equity_account = Account(name="Equity", code="3000", type="Equity")
        db.session.add(equity_account)
        db.session.commit()
        jel2 = JournalEntryLine(journal_entry_id=je.id, account_id=equity_account.id, debit=Decimal('0.00'), credit=Decimal('5000.00'))
        db_session = db.session
        db_session.add(jel2)
        db_session.commit()
        
        # Create Customer and Vendor
        customer = Customer(name="Test Customer", email="test@example.com")
        vendor = Vendor(name="Test Vendor", email="vendor@example.com")
        db_session.add(customer)
        db_session.add(vendor)
        db_session.commit()
        
        # Create accounts for invoice/bill lines
        revenue_account = Account(name="Sales", code="4000", type="Revenue")
        expense_account = Account(name="Supplies", code="5000", type="Expense")
        db_session.add_all([revenue_account, expense_account])
        db_session.commit()

        # Create Invoice (Revenue)
        invoice = Invoice(customer_id=customer.id, invoice_number="INV-001", issue_date=date.today(), due_date=date.today(), status='draft')
        db_session.add(invoice)
        line1 = InvoiceLine(description="Services", quantity=1, unit_price=Decimal('1000.00'), account_id=revenue_account.id)
        invoice.lines.append(line1)
        db_session.commit()
        
        # Create Bill (Expense)
        bill = Bill(vendor_id=vendor.id, bill_number="BILL-001", issue_date=date.today(), due_date=date.today(), status='draft')
        db_session.add(bill)
        bline1 = BillLine(description="Materials", quantity=1, unit_cost=Decimal('400.00'), account_id=expense_account.id)
        bill.lines.append(bline1)
        db_session.commit()

    # 2. Call dashboard endpoint
    response = client.get('/api/dashboard', headers=auth_headers)
    assert response.status_code == 200
    data = response.get_json()
    
    # 3. Verify metrics
    assert data['metrics']['revenue'] == 1000.00
    assert data['metrics']['expenses'] == 400.00
    assert data['metrics']['net_income'] == 600.00
    assert data['metrics']['outstanding_ar'] == 1000.00
    assert data['metrics']['outstanding_ap'] == 400.00
    assert data['metrics']['cash_balance'] == 5000.00
