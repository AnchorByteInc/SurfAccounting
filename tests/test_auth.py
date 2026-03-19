import pytest
from backend.app import create_app
from backend.config import Config
from backend.extensions import db

class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True
    AUTH_USER = "testadmin"
    AUTH_PASS = "testpass"

@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    return app.test_client()

def test_login_success(client):
    response = client.post('/api/auth/login', json={
        "username": "testadmin",
        "password": "testpass"
    })
    assert response.status_code == 200
    assert 'access_token' in response.get_json()

def test_login_failure(client):
    response = client.post('/api/auth/login', json={
        "username": "testadmin",
        "password": "wrongpassword"
    })
    assert response.status_code == 401
    assert 'access_token' not in response.get_json()

def test_protected_route_without_token(client):
    # /api/customers/status is a protected route
    response = client.get('/api/customers/status')
    assert response.status_code == 401
    assert response.get_json()['msg'] is not None

def test_protected_route_with_valid_token(client):
    # First login
    login_response = client.post('/api/auth/login', json={
        "username": "testadmin",
        "password": "testpass"
    })
    token = login_response.get_json()['access_token']
    
    # Then access protected route
    response = client.get('/api/customers/status', headers={
        "Authorization": f"Bearer {token}"
    })
    assert response.status_code == 200
    assert response.get_json() == {"status": "customers blueprint active"}

def test_protected_route_with_invalid_token(client):
    response = client.get('/api/customers/status', headers={
        "Authorization": "Bearer invalidtoken"
    })
    assert response.status_code in [401, 422]

def test_public_health_route(client):
    response = client.get('/health')
    assert response.status_code == 200
    assert response.get_json()['status'] == "healthy"
