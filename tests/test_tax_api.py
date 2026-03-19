import pytest
from backend.app import create_app
from backend.config import Config
from backend.extensions import db
from backend.models.tax import Tax

class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True
    JWT_SECRET_KEY = 'test-secret-at-least-32-bytes-long-for-security-purposes'

@pytest.fixture
def client():
    app = create_app(TestConfig)
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.drop_all()

@pytest.fixture
def auth_headers(client):
    # Register and login to get a token
    # Alternatively, bypass JWT for testing if allowed, but here app.before_request protects routes.
    # In this project, there's usually a way to get a token.
    # Let's check how other tests do it.
    from flask_jwt_extended import create_access_token
    with client.application.app_context():
        token = create_access_token(identity='test-user')
        return {'Authorization': f'Bearer {token}'}

def test_tax_api(client, auth_headers):
    # Create
    response = client.post('/api/taxes', json={
        'name': 'GST',
        'rate': '0.07',
        'description': 'Goods and Services Tax'
    }, headers=auth_headers)
    assert response.status_code == 201
    assert response.json['name'] == 'GST'
    assert response.json['rate'] == '0.0700'
    tax_id = response.json['id']

    # Get List
    response = client.get('/api/taxes', headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json['taxes']) == 1

    # Update
    response = client.put(f'/api/taxes/{tax_id}', json={
        'rate': '0.08'
    }, headers=auth_headers)
    assert response.status_code == 200
    assert response.json['rate'] == '0.0800'

    # Delete
    response = client.delete(f'/api/taxes/{tax_id}', headers=auth_headers)
    assert response.status_code == 200
    
    # Get List again
    response = client.get('/api/taxes', headers=auth_headers)
    assert len(response.json['taxes']) == 0
