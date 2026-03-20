import pytest
from backend.app import create_app
from backend.config import Config
from backend.extensions import db
from backend.models.customer import Customer
from backend.models.invoice import Invoice
from backend.models.account import Account
from backend.models.tax import Tax
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
        # Seed settings for tax calculation
        db.session.add(Settings(business_name="Test Biz"))
        # Seed an account for invoice lines
        db.session.add(Account(name="Sales", code="4000", type="Revenue"))
        # Seed a tax
        db.session.add(Tax(name="Tax", rate=0.10))
        # Seed a customer
        db.session.add(Customer(name="Test Customer", email="test@example.com"))
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

def test_create_invoice(client, auth_headers, app):
    with app.app_context():
        customer_id = Customer.query.first().id
        account_id = Account.query.first().id
        tax_id = Tax.query.first().id
    
    data = {
        "customer_id": customer_id,
        "invoice_number": "INV-001",
        "issue_date": date.today().isoformat(),
        "due_date": (date.today() + timedelta(days=30)).isoformat(),
        "lines": [
            {
                "description": "Consulting",
                "quantity": 10,
                "unit_price": 100,
                "account_id": account_id,
                "tax_ids": [tax_id]
            }
        ]
    }
    response = client.post('/api/invoices', json=data, headers=auth_headers)
    if response.status_code != 201:
        print(response.get_json())
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['invoice_number'] == "INV-001"
    # subtotal = 10 * 100 = 1000
    # tax = 1000 * 0.10 = 100
    # total = 1100
    assert float(json_data['subtotal']) == 1000.0
    assert float(json_data['tax']) == 100.0
    assert float(json_data['total']) == 1100.0
    assert len(json_data['lines']) == 1
    assert float(json_data['lines'][0]['line_total']) == 1000.0

def test_get_invoices_pagination_and_filtering(client, auth_headers, app):
    with app.app_context():
        customer = Customer.query.first()
        for i in range(15):
            inv = Invoice(
                customer_id=customer.id,
                invoice_number=f"INV-{i:03d}",
                issue_date=date.today(),
                due_date=date.today() + timedelta(days=30),
                status='draft' if i % 2 == 0 else 'sent'
            )
            db.session.add(inv)
        db.session.commit()
    
    # Page 1
    response = client.get('/api/invoices?page=1&per_page=10', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['invoices']) == 10
    assert json_data['total'] == 15
    
    # Filter by status
    response = client.get('/api/invoices?status=sent', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert all(inv['status'] == 'sent' for inv in json_data['invoices'])
    
    # Filter by invoice number
    response = client.get('/api/invoices?invoice_number=INV-005', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['invoices']) == 1
    assert json_data['invoices'][0]['invoice_number'] == "INV-005"

def test_update_invoice(client, auth_headers, app):
    with app.app_context():
        customer = Customer.query.first()
        inv = Invoice(
            customer_id=customer.id,
            invoice_number="INV-UPDATE",
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30)
        )
        db.session.add(inv)
        db.session.commit()
        invoice_id = inv.id
        
    data = {"status": "sent"}
    response = client.put(f'/api/invoices/{invoice_id}', json=data, headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()['status'] == "sent"

def test_delete_invoice(client, auth_headers, app):
    with app.app_context():
        customer = Customer.query.first()
        inv = Invoice(
            customer_id=customer.id,
            invoice_number="INV-DELETE",
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30)
        )
        db.session.add(inv)
        db.session.commit()
        invoice_id = inv.id
        
    response = client.delete(f'/api/invoices/{invoice_id}', headers=auth_headers)
    assert response.status_code == 200
    
    response = client.get(f'/api/invoices/{invoice_id}', headers=auth_headers)
    assert response.status_code == 404

def test_create_invoice_missing_data(client, auth_headers):
    data = {
        "invoice_number": "INV-MISSING"
    }
    response = client.post('/api/invoices', json=data, headers=auth_headers)
    assert response.status_code == 400
    json_data = response.get_json()
    # Marshmallow returns error for required fields
    assert 'customer_id' in json_data
    assert 'issue_date' in json_data
    assert 'due_date' in json_data
