import pytest
from backend.app import create_app
from backend.config import Config
from backend.extensions import db
from backend.models.account import Account

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


def test_create_account(client, auth_headers):
    data = {
        "name": "Cash",
        "code": "1000",
        "type": "Asset",
        "subtype": "Bank",
        "is_active": True
    }
    response = client.post('/api/accounts', json=data, headers=auth_headers)
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['name'] == "Cash"
    assert json_data['code'] == "1000"
    assert json_data['type'] == "Asset"


def test_create_account_missing_name(client, auth_headers):
    data = {
        "code": "1001",
        "type": "Asset"
    }
    response = client.post('/api/accounts', json=data, headers=auth_headers)
    assert response.status_code == 400
    assert 'name' in response.get_json()


def test_create_account_invalid_type(client, auth_headers):
    data = {
        "name": "Weird",
        "code": "1002",
        "type": "Unknown"
    }
    response = client.post('/api/accounts', json=data, headers=auth_headers)
    assert response.status_code == 400
    assert 'type' in response.get_json()


def test_create_account_duplicate_code(client, auth_headers, app):
    with app.app_context():
        db.session.add(Account(name="Existing", code="2000", type="Asset"))
        db.session.commit()
    data = {
        "name": "Another",
        "code": "2000",
        "type": "Asset"
    }
    response = client.post('/api/accounts', json=data, headers=auth_headers)
    assert response.status_code == 400
    assert "Account code already exists" in response.get_json()['message']


def test_get_accounts_pagination(client, auth_headers, app):
    with app.app_context():
        for i in range(15):
            db.session.add(Account(name=f"Account {i}", code=f"{3000 + i}", type="Asset"))
        db.session.commit()

    # Page 1
    response = client.get('/api/accounts?page=1&per_page=10', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['accounts']) == 10
    assert json_data['total'] == 15
    assert json_data['pages'] == 2

    # Page 2
    response = client.get('/api/accounts?page=2&per_page=10', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['accounts']) == 5


def test_get_accounts_filtering(client, auth_headers, app):
    with app.app_context():
        a1 = Account(name="Cash", code="1100", type="Asset", subtype="Bank", is_active=True)
        a2 = Account(name="Accounts Payable", code="2100", type="Liability", subtype="Current", is_active=False)
        db.session.add_all([a1, a2])
        db.session.commit()

    # Filter by name
    response = client.get('/api/accounts?name=Cash', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['accounts']) == 1
    assert json_data['accounts'][0]['name'] == "Cash"

    # Filter by code (partial)
    response = client.get('/api/accounts?code=210', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['accounts']) == 1
    assert json_data['accounts'][0]['code'] == "2100"

    # Filter by type
    response = client.get('/api/accounts?type=Liability', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['accounts']) == 1
    assert json_data['accounts'][0]['type'] == "Liability"

    # Filter by type (case-insensitive)
    response = client.get('/api/accounts?type=liability', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['accounts']) == 1
    assert json_data['accounts'][0]['type'] == "Liability"

    response = client.get('/api/accounts?type=LIABILITY', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['accounts']) == 1
    assert json_data['accounts'][0]['type'] == "Liability"

    # Filter by is_active
    response = client.get('/api/accounts?is_active=false', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['accounts']) == 1
    assert json_data['accounts'][0]['is_active'] is False


def test_get_single_account(client, auth_headers, app):
    with app.app_context():
        a = Account(name="Receivables", code="1200", type="Asset")
        db.session.add(a)
        db.session.commit()
        account_id = a.id

    response = client.get(f'/api/accounts/{account_id}', headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()['name'] == "Receivables"


def test_update_account(client, auth_headers, app):
    with app.app_context():
        a = Account(name="Old Name", code="1300", type="Asset")
        db.session.add(a)
        db.session.commit()
        account_id = a.id

    data = {"name": "New Name"}
    response = client.put(f'/api/accounts/{account_id}', json=data, headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()['name'] == "New Name"
    assert response.get_json()['code'] == "1300"


def test_delete_account(client, auth_headers, app):
    with app.app_context():
        a = Account(name="To Delete", code="1400", type="Asset")
        db.session.add(a)
        db.session.commit()
        account_id = a.id

    response = client.delete(f'/api/accounts/{account_id}', headers=auth_headers)
    assert response.status_code == 200

    response = client.get(f'/api/accounts/{account_id}', headers=auth_headers)
    assert response.status_code == 404
