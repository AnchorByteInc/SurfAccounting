import pytest
from backend.app import create_app
from backend.config import Config
from backend.extensions import db
from backend.models.vendor import Vendor

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

def test_create_vendor(client, auth_headers):
    data = {
        "name": "New Vendor",
        "primary_contact_name": "John Doe",
        "email": "vendor@example.com",
        "phone": "9876543210",
        "address": "456 Avenue"
    }
    response = client.post('/api/vendors', json=data, headers=auth_headers)
    assert response.status_code == 201
    assert response.get_json()['name'] == "New Vendor"
    assert response.get_json()['primary_contact_name'] == "John Doe"
    assert response.get_json()['email'] == "vendor@example.com"

def test_create_vendor_invalid_email(client, auth_headers):
    data = {
        "name": "Invalid Vendor",
        "email": "not-an-email"
    }
    response = client.post('/api/vendors', json=data, headers=auth_headers)
    assert response.status_code == 400
    assert 'email' in response.get_json()

def test_create_vendor_missing_name(client, auth_headers):
    data = {
        "email": "missing@example.com"
    }
    response = client.post('/api/vendors', json=data, headers=auth_headers)
    assert response.status_code == 400
    assert 'name' in response.get_json()

def test_get_vendors_pagination(client, auth_headers, app):
    with app.app_context():
        for i in range(15):
            db.session.add(Vendor(name=f"Vendor {i}", email=f"v{i}@example.com"))
        db.session.commit()
    
    # Page 1
    response = client.get('/api/vendors?page=1&per_page=10', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['vendors']) == 10
    assert json_data['total'] == 15
    assert json_data['pages'] == 2
    
    # Page 2
    response = client.get('/api/vendors?page=2&per_page=10', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['vendors']) == 5

def test_get_vendors_filtering(client, auth_headers, app):
    with app.app_context():
        db.session.add(Vendor(name="Vendor A", email="a@example.com"))
        db.session.add(Vendor(name="Vendor B", email="b@example.com"))
        db.session.commit()
    
    # Filter by name
    response = client.get('/api/vendors?name=Vendor A', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['vendors']) == 1
    assert json_data['vendors'][0]['name'] == "Vendor A"
    
    # Filter by email
    response = client.get('/api/vendors?email=b@', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['vendors']) == 1
    assert json_data['vendors'][0]['name'] == "Vendor B"

def test_get_single_vendor(client, auth_headers, app):
    with app.app_context():
        v = Vendor(name="Test One", email="one@example.com")
        db.session.add(v)
        db.session.commit()
        vendor_id = v.id
    
    response = client.get(f'/api/vendors/{vendor_id}', headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()['name'] == "Test One"

def test_update_vendor(client, auth_headers, app):
    with app.app_context():
        v = Vendor(name="Old Name", email="old@example.com")
        db.session.add(v)
        db.session.commit()
        vendor_id = v.id
    
    data = {"name": "New Name"}
    response = client.put(f'/api/vendors/{vendor_id}', json=data, headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()['name'] == "New Name"
    assert response.get_json()['email'] == "old@example.com"

def test_delete_vendor(client, auth_headers, app):
    with app.app_context():
        v = Vendor(name="To Delete", email="delete@example.com")
        db.session.add(v)
        db.session.commit()
        vendor_id = v.id
    
    response = client.delete(f'/api/vendors/{vendor_id}', headers=auth_headers)
    assert response.status_code == 200
    
    response = client.get(f'/api/vendors/{vendor_id}', headers=auth_headers)
    assert response.status_code == 404

def test_create_vendor_duplicate_email(client, auth_headers, app):
    with app.app_context():
        db.session.add(Vendor(name="Existing", email="duplicate@example.com"))
        db.session.commit()
    
    data = {
        "name": "Another",
        "email": "duplicate@example.com"
    }
    response = client.post('/api/vendors', json=data, headers=auth_headers)
    assert response.status_code == 400
    assert "Email already exists" in response.get_json()['message']
