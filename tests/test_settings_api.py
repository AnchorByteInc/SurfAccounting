import pytest
from backend.app import create_app
from backend.config import Config
from backend.extensions import db
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

def test_create_settings(client, auth_headers):
    data = {
        "business_name": "My Business",
        "address": "123 Business Way",
        "default_currency": "USD"
    }
    response = client.post('/api/settings', json=data, headers=auth_headers)
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['business_name'] == "My Business"


def test_get_settings_pagination(client, auth_headers, app):
    with app.app_context():
        for i in range(15):
            db.session.add(Settings(business_name=f"Business {i}", default_currency="USD"))
        db.session.commit()
    
    # Page 1
    response = client.get('/api/settings?page=1&per_page=10', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['settings']) == 10
    assert json_data['total'] == 15
    assert json_data['pages'] == 2
    
    # Page 2
    response = client.get('/api/settings?page=2&per_page=10', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['settings']) == 5

def test_get_settings_filtering(client, auth_headers, app):
    with app.app_context():
        db.session.add(Settings(business_name="Alpha", default_currency="USD"))
        db.session.add(Settings(business_name="Beta", default_currency="EUR"))
        db.session.commit()
    
    # Filter by name
    response = client.get('/api/settings?business_name=Alpha', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['settings']) == 1
    assert json_data['settings'][0]['business_name'] == "Alpha"
    
    # Filter by currency
    response = client.get('/api/settings?default_currency=EUR', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['settings']) == 1
    assert json_data['settings'][0]['business_name'] == "Beta"

def test_get_single_settings(client, auth_headers, app):
    with app.app_context():
        s = Settings(business_name="Test Business")
        db.session.add(s)
        db.session.commit()
        settings_id = s.id
    
    response = client.get(f'/api/settings/{settings_id}', headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()['business_name'] == "Test Business"

def test_update_settings(client, auth_headers, app):
    with app.app_context():
        s = Settings(business_name="Old Name")
        db.session.add(s)
        db.session.commit()
        settings_id = s.id
    
    data = {"business_name": "New Name"}
    response = client.put(f'/api/settings/{settings_id}', json=data, headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()['business_name'] == "New Name"

def test_delete_settings(client, auth_headers, app):
    with app.app_context():
        s = Settings(business_name="To Delete")
        db.session.add(s)
        db.session.commit()
        settings_id = s.id
    
    response = client.delete(f'/api/settings/{settings_id}', headers=auth_headers)
    assert response.status_code == 200
    
    response = client.get(f'/api/settings/{settings_id}', headers=auth_headers)
    assert response.status_code == 404
