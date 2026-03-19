import pytest
from datetime import date
from backend.app import create_app
from backend.config import Config
from backend.extensions import db
from backend.models.invoice import Invoice, InvoiceLine
from backend.models.customer import Customer
from backend.models.account import Account
from backend.models.settings import Settings

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
        db.session.add(Settings(business_name="Test Co"))
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

@pytest.fixture
def setup_data(app):
    with app.app_context():
        customer = Customer(name="Test Customer", email="test@example.com")
        account = Account(name="Sales", code="4000", type="Revenue")
        db.session.add(customer)
        db.session.add(account)
        db.session.commit()
        
        invoice = Invoice(customer_id=customer.id, invoice_number="INV-001", 
                          issue_date=date(2023, 1, 1), due_date=date(2023, 1, 31))
        db.session.add(invoice)
        db.session.commit()
        
        return {
            "customer_id": customer.id,
            "account_id": account.id,
            "invoice_id": invoice.id
        }

def test_create_invoice_line(client, auth_headers, setup_data):
    data = {
        "invoice_id": setup_data["invoice_id"],
        "account_id": setup_data["account_id"],
        "description": "Consulting services",
        "quantity": 10,
        "unit_price": 150.0
    }
    response = client.post('/api/invoice_lines', json=data, headers=auth_headers)
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['description'] == "Consulting services"
    assert float(json_data['line_total']) == 1500.0

def test_get_invoice_lines_pagination(client, auth_headers, setup_data, app):
    with app.app_context():
        for i in range(15):
            db.session.add(InvoiceLine(
                invoice_id=setup_data["invoice_id"],
                account_id=setup_data["account_id"],
                description=f"Line {i}",
                quantity=1,
                unit_price=10.0
            ))
        db.session.commit()
    
    # Page 1
    response = client.get(f'/api/invoice_lines?page=1&per_page=10&invoice_id={setup_data["invoice_id"]}', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['invoice_lines']) == 10
    assert json_data['total'] == 15
    assert json_data['pages'] == 2
    
    # Page 2
    response = client.get(f'/api/invoice_lines?page=2&per_page=10&invoice_id={setup_data["invoice_id"]}', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['invoice_lines']) == 5

def test_get_invoice_lines_filtering(client, auth_headers, setup_data, app):
    with app.app_context():
        db.session.add(InvoiceLine(
            invoice_id=setup_data["invoice_id"],
            account_id=setup_data["account_id"],
            description="Specific Line",
            quantity=1,
            unit_price=10.0
        ))
        db.session.commit()
    
    # Filter by description
    response = client.get(f'/api/invoice_lines?description=Specific', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['invoice_lines']) == 1
    assert json_data['invoice_lines'][0]['description'] == "Specific Line"

def test_get_single_invoice_line(client, auth_headers, setup_data, app):
    with app.app_context():
        line = InvoiceLine(
            invoice_id=setup_data["invoice_id"],
            account_id=setup_data["account_id"],
            description="Single Line",
            quantity=1,
            unit_price=50.0
        )
        db.session.add(line)
        db.session.commit()
        line_id = line.id
    
    response = client.get(f'/api/invoice_lines/{line_id}', headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()['description'] == "Single Line"

def test_update_invoice_line(client, auth_headers, setup_data, app):
    with app.app_context():
        line = InvoiceLine(
            invoice_id=setup_data["invoice_id"],
            account_id=setup_data["account_id"],
            description="Old Description",
            quantity=1,
            unit_price=50.0
        )
        db.session.add(line)
        db.session.commit()
        line_id = line.id
    
    data = {"description": "New Description", "quantity": 2}
    response = client.put(f'/api/invoice_lines/{line_id}', json=data, headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()['description'] == "New Description"
    assert float(response.get_json()['line_total']) == 100.0

def test_delete_invoice_line(client, auth_headers, setup_data, app):
    with app.app_context():
        line = InvoiceLine(
            invoice_id=setup_data["invoice_id"],
            account_id=setup_data["account_id"],
            description="To Delete",
            quantity=1,
            unit_price=50.0
        )
        db.session.add(line)
        db.session.commit()
        line_id = line.id
    
    response = client.delete(f'/api/invoice_lines/{line_id}', headers=auth_headers)
    assert response.status_code == 200
    
    response = client.get(f'/api/invoice_lines/{line_id}', headers=auth_headers)
    assert response.status_code == 404

def test_create_invoice_line_invalid_account(client, auth_headers, setup_data):
    data = {
        "invoice_id": setup_data["invoice_id"],
        "account_id": 9999, # Non-existent account
        "description": "Invalid line",
        "quantity": 1,
        "unit_price": 10.0
    }
    response = client.post('/api/invoice_lines', json=data, headers=auth_headers)
    assert response.status_code == 400
    # Integrity error or validation error should occur
