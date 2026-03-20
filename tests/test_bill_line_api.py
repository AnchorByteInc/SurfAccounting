import pytest
from datetime import date
from backend.app import create_app
from backend.config import Config
from backend.extensions import db
from backend.models.bill import Bill, BillLine
from backend.models.vendor import Vendor
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
        # Seed settings for tax calculation (though not strictly needed for bills right now)
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
        vendor = Vendor(name="Test Vendor", email="test@vendor.com")
        account = Account(name="Office Supplies", code="5000", type="Expense")
        db.session.add(vendor)
        db.session.add(account)
        db.session.commit()
        
        bill = Bill(vendor_id=vendor.id, bill_number="BILL-001", 
                    issue_date=date(2023, 1, 1), due_date=date(2023, 1, 31))
        db.session.add(bill)
        db.session.commit()
        
        return {
            "vendor_id": vendor.id,
            "account_id": account.id,
            "bill_id": bill.id
        }

def test_create_bill_line(client, auth_headers, setup_data):
    data = {
        "bill_id": setup_data["bill_id"],
        "account_id": setup_data["account_id"],
        "description": "Pens and paper",
        "quantity": 10,
        "unit_cost": 5.0
    }
    response = client.post('/api/bill_lines', json=data, headers=auth_headers)
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['description'] == "Pens and paper"
    assert float(json_data['line_total']) == 50.0

def test_get_bill_lines_pagination(client, auth_headers, setup_data, app):
    with app.app_context():
        for i in range(15):
            db.session.add(BillLine(
                bill_id=setup_data["bill_id"],
                account_id=setup_data["account_id"],
                description=f"Line {i}",
                quantity=1,
                unit_cost=10.0
            ))
        db.session.commit()
    
    # Page 1
    response = client.get(f'/api/bill_lines?page=1&per_page=10&bill_id={setup_data["bill_id"]}', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['bill_lines']) == 10
    assert json_data['total'] == 15
    assert json_data['pages'] == 2
    
    # Page 2
    response = client.get(f'/api/bill_lines?page=2&per_page=10&bill_id={setup_data["bill_id"]}', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['bill_lines']) == 5

def test_get_bill_lines_filtering(client, auth_headers, setup_data, app):
    with app.app_context():
        db.session.add(BillLine(
            bill_id=setup_data["bill_id"],
            account_id=setup_data["account_id"],
            description="Specific Line",
            quantity=1,
            unit_cost=10.0
        ))
        db.session.commit()
    
    # Filter by description
    response = client.get('/api/bill_lines?description=Specific', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['bill_lines']) == 1
    assert json_data['bill_lines'][0]['description'] == "Specific Line"

def test_get_single_bill_line(client, auth_headers, setup_data, app):
    with app.app_context():
        line = BillLine(
            bill_id=setup_data["bill_id"],
            account_id=setup_data["account_id"],
            description="Single Line",
            quantity=1,
            unit_cost=50.0
        )
        db.session.add(line)
        db.session.commit()
        line_id = line.id
    
    response = client.get(f'/api/bill_lines/{line_id}', headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()['description'] == "Single Line"

def test_update_bill_line(client, auth_headers, setup_data, app):
    with app.app_context():
        line = BillLine(
            bill_id=setup_data["bill_id"],
            account_id=setup_data["account_id"],
            description="Old Description",
            quantity=1,
            unit_cost=50.0
        )
        db.session.add(line)
        db.session.commit()
        line_id = line.id
    
    data = {"description": "New Description", "quantity": 2}
    response = client.put(f'/api/bill_lines/{line_id}', json=data, headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()['description'] == "New Description"
    assert float(response.get_json()['line_total']) == 100.0

def test_delete_bill_line(client, auth_headers, setup_data, app):
    with app.app_context():
        line = BillLine(
            bill_id=setup_data["bill_id"],
            account_id=setup_data["account_id"],
            description="To Delete",
            quantity=1,
            unit_cost=50.0
        )
        db.session.add(line)
        db.session.commit()
        line_id = line.id
    
    response = client.delete(f'/api/bill_lines/{line_id}', headers=auth_headers)
    assert response.status_code == 200
    
    response = client.get(f'/api/bill_lines/{line_id}', headers=auth_headers)
    assert response.status_code == 404

def test_create_bill_line_invalid_account(client, auth_headers, setup_data):
    data = {
        "bill_id": setup_data["bill_id"],
        "account_id": 9999, # Non-existent account
        "description": "Invalid line",
        "quantity": 1,
        "unit_cost": 10.0
    }
    response = client.post('/api/bill_lines', json=data, headers=auth_headers)
    assert response.status_code == 400
    json_data = response.get_json()
    assert "account_id" in json_data
    assert "Account does not exist" in json_data["account_id"]
