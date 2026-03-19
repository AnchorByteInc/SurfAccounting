import pytest
from backend.app import create_app
from backend.config import Config
from backend.extensions import db
from backend.models.vendor import Vendor
from backend.models.bill import Bill, BillLine
from backend.models.account import Account
from backend.models.settings import Settings
from datetime import date, timedelta

class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        # Seed settings
        db.session.add(Settings(business_name="Test Biz"))
        # Seed an account for bill lines
        db.session.add(Account(name="Expenses", code="5000", type="Expense"))
        # Seed Accounts Payable
        db.session.add(Account(name="Accounts Payable", code="2000", type="Liability", subtype="Accounts Payable"))
        # Seed a vendor
        db.session.add(Vendor(name="Test Vendor", email="vendor@example.com"))
        db.session.commit()
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

def test_create_bill(client, auth_headers, app):
    with app.app_context():
        vendor_id = Vendor.query.first().id
        account_id = Account.query.first().id
    
    data = {
        "vendor_id": vendor_id,
        "bill_number": "BILL-001",
        "issue_date": date.today().isoformat(),
        "due_date": (date.today() + timedelta(days=30)).isoformat(),
        "lines": [
            {
                "description": "Office Supplies",
                "quantity": 5,
                "unit_cost": 20,
                "account_id": account_id
            }
        ]
    }
    response = client.post('/api/bills', json=data, headers=auth_headers)
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['bill_number'] == "BILL-001"
    # total = 5 * 20 = 100
    assert float(json_data['total']) == 100.0
    assert float(json_data['balance']) == 100.0
    assert len(json_data['lines']) == 1
    assert float(json_data['lines'][0]['line_total']) == 100.0

def test_get_bills_pagination_and_filtering(client, auth_headers, app):
    with app.app_context():
        vendor = Vendor.query.first()
        for i in range(15):
            bill = Bill(
                vendor_id=vendor.id,
                bill_number=f"BILL-{i:03d}",
                issue_date=date.today(),
                due_date=date.today() + timedelta(days=30),
                status='draft' if i % 2 == 0 else 'paid'
            )
            db.session.add(bill)
        db.session.commit()
    
    # Page 1
    response = client.get('/api/bills?page=1&per_page=10', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['bills']) == 10
    assert json_data['total'] == 15
    
    # Filter by status
    response = client.get('/api/bills?status=paid', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert all(bill['status'] == 'paid' for bill in json_data['bills'])
    
    # Filter by bill number
    response = client.get('/api/bills?bill_number=BILL-005', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['bills']) == 1
    assert json_data['bills'][0]['bill_number'] == "BILL-005"

def test_update_bill(client, auth_headers, app):
    with app.app_context():
        vendor = Vendor.query.first()
        bill = Bill(
            vendor_id=vendor.id,
            bill_number="BILL-UPDATE",
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30)
        )
        db.session.add(bill)
        db.session.commit()
        bill_id = bill.id
        
    data = {"status": "paid"}
    response = client.put(f'/api/bills/{bill_id}', json=data, headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()['status'] == "paid"

def test_delete_bill(client, auth_headers, app):
    with app.app_context():
        vendor = Vendor.query.first()
        bill = Bill(
            vendor_id=vendor.id,
            bill_number="BILL-DELETE",
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30)
        )
        db.session.add(bill)
        db.session.commit()
        bill_id = bill.id
        
    response = client.delete(f'/api/bills/{bill_id}', headers=auth_headers)
    assert response.status_code == 200
    
    response = client.get(f'/api/bills/{bill_id}', headers=auth_headers)
    assert response.status_code == 404

def test_create_bill_missing_data(client, auth_headers):
    data = {
        "bill_number": "BILL-MISSING"
    }
    response = client.post('/api/bills', json=data, headers=auth_headers)
    assert response.status_code == 400
    json_data = response.get_json()
    # Marshmallow returns error for required fields
    assert 'vendor_id' in json_data
    assert 'issue_date' in json_data
    assert 'due_date' in json_data
