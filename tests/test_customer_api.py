import pytest
from backend.app import create_app
from backend.config import Config
from backend.extensions import db
from backend.models.customer import Customer

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

def test_create_customer(client, auth_headers):
    data = {
        "name": "New Customer",
        "email": "new@example.com",
        "phone": "1234567890",
        "billing_address": "123 Street"
    }
    response = client.post('/api/customers', json=data, headers=auth_headers)
    assert response.status_code == 201
    assert response.get_json()['name'] == "New Customer"
    assert response.get_json()['email'] == "new@example.com"

def test_create_customer_with_new_fields(client, auth_headers):
    data = {
        "name": "Full Customer",
        "primary_contact_name": "John Doe",
        "email": "full@example.com",
        "phone": "555-1234",
        "website": "https://example.com",
        "billing_address": "123 Billing St",
        "shipping_address": "456 Shipping Ave"
    }
    response = client.post('/api/customers', json=data, headers=auth_headers)
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['name'] == "Full Customer"
    assert json_data['primary_contact_name'] == "John Doe"
    assert json_data['email'] == "full@example.com"
    assert json_data['phone'] == "555-1234"
    assert json_data['website'] == "https://example.com"
    assert json_data['billing_address'] == "123 Billing St"
    assert json_data['shipping_address'] == "456 Shipping Ave"

def test_create_customer_invalid_email(client, auth_headers):
    data = {
        "name": "Invalid Customer",
        "email": "not-an-email"
    }
    response = client.post('/api/customers', json=data, headers=auth_headers)
    assert response.status_code == 400
    assert 'email' in response.get_json()

def test_create_customer_missing_name(client, auth_headers):
    data = {
        "email": "missing@example.com"
    }
    response = client.post('/api/customers', json=data, headers=auth_headers)
    assert response.status_code == 400
    assert 'name' in response.get_json()

def test_get_customers_pagination(client, auth_headers, app):
    with app.app_context():
        for i in range(15):
            db.session.add(Customer(name=f"Customer {i}", email=f"c{i}@example.com"))
        db.session.commit()
    
    # Page 1
    response = client.get('/api/customers?page=1&per_page=10', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['customers']) == 10
    assert json_data['total'] == 15
    assert json_data['pages'] == 2
    
    # Page 2
    response = client.get('/api/customers?page=2&per_page=10', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['customers']) == 5

def test_get_customers_filtering(client, auth_headers, app):
    with app.app_context():
        db.session.add(Customer(name="Alice", email="alice@example.com"))
        db.session.add(Customer(name="Bob", email="bob@example.com"))
        db.session.commit()
    
    # Filter by name
    response = client.get('/api/customers?name=Alice', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['customers']) == 1
    assert json_data['customers'][0]['name'] == "Alice"
    
    # Filter by email
    response = client.get('/api/customers?email=bob@', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['customers']) == 1
    assert json_data['customers'][0]['name'] == "Bob"

def test_get_single_customer(client, auth_headers, app):
    with app.app_context():
        c = Customer(name="Test One", email="one@example.com")
        db.session.add(c)
        db.session.commit()
        customer_id = c.id
    
    response = client.get(f'/api/customers/{customer_id}', headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()['name'] == "Test One"

def test_update_customer(client, auth_headers, app):
    with app.app_context():
        c = Customer(name="Old Name", email="old@example.com")
        db.session.add(c)
        db.session.commit()
        customer_id = c.id
    
    data = {"name": "New Name"}
    response = client.put(f'/api/customers/{customer_id}', json=data, headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()['name'] == "New Name"
    assert response.get_json()['email'] == "old@example.com"

def test_delete_customer(client, auth_headers, app):
    with app.app_context():
        c = Customer(name="To Delete", email="delete@example.com")
        db.session.add(c)
        db.session.commit()
        customer_id = c.id
    
    response = client.delete(f'/api/customers/{customer_id}', headers=auth_headers)
    assert response.status_code == 200
    
    response = client.get(f'/api/customers/{customer_id}', headers=auth_headers)
    assert response.status_code == 404

def test_create_customer_duplicate_email(client, auth_headers, app):
    with app.app_context():
        db.session.add(Customer(name="Existing", email="duplicate@example.com"))
        db.session.commit()
    
    data = {
        "name": "Another",
        "email": "duplicate@example.com"
    }
    response = client.post('/api/customers', json=data, headers=auth_headers)
    assert response.status_code == 400
    assert "Email already exists" in response.get_json()['message']
