import pytest
from backend.app import create_app
from backend.config import Config
from backend.extensions import db
from backend.models.account import Account
from backend.models.bank import BankAccount


class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        # Seed an account to reference in bank accounts
        acc = Account(name="Cash", code="1000", type="Asset", subtype="Bank")
        db.session.add(acc)
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


def test_create_bank_account(client, auth_headers, app):
    with app.app_context():
        account_id = Account.query.first().id

    data = {
        "name": "Main Checking",
        "account_number": "123456789",
        "account_id": account_id
    }
    response = client.post('/api/bank_accounts', json=data, headers=auth_headers)
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['name'] == "Main Checking"
    assert json_data['account_number'] == "123456789"
    assert json_data['account_id'] == account_id


def test_create_bank_account_missing_name(client, auth_headers, app):
    with app.app_context():
        account_id = Account.query.first().id

    data = {
        "account_number": "987654321",
        "account_id": account_id
    }
    response = client.post('/api/bank_accounts', json=data, headers=auth_headers)
    assert response.status_code == 400
    assert 'name' in response.get_json()


def test_create_bank_account_invalid_account(client, auth_headers):
    data = {
        "name": "Invalid Account Ref",
        "account_id": 99999
    }
    response = client.post('/api/bank_accounts', json=data, headers=auth_headers)
    assert response.status_code == 400
    resp = response.get_json()
    # Could be under 'account_id' key depending on marshmallow
    assert ('account_id' in resp and 'does not exist' in str(resp['account_id'])) or 'Account does not exist' in str(resp)


def test_get_bank_accounts_pagination_and_filtering(client, auth_headers, app):
    with app.app_context():
        account_id = Account.query.first().id
        for i in range(15):
            db.session.add(BankAccount(name=f"Bank {i}", account_number=f"ACC-{i:03d}", account_id=account_id))
        db.session.commit()

    # Page 1
    response = client.get('/api/bank_accounts?page=1&per_page=10', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['bank_accounts']) == 10
    assert json_data['total'] == 15

    # Filter by name
    response = client.get('/api/bank_accounts?name=Bank 1', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['bank_accounts']) >= 1
    assert any('Bank 1' in ba['name'] for ba in json_data['bank_accounts'])

    # Filter by account_number
    response = client.get('/api/bank_accounts?account_number=ACC-005', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['bank_accounts']) == 1
    assert json_data['bank_accounts'][0]['account_number'] == 'ACC-005'

    # Filter by account_id
    response = client.get(f'/api/bank_accounts?account_id={account_id}', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert json_data['total'] == 15


def test_get_single_bank_account(client, auth_headers, app):
    with app.app_context():
        account_id = Account.query.first().id
        ba = BankAccount(name="One Bank", account_number="ONE-001", account_id=account_id)
        db.session.add(ba)
        db.session.commit()
        ba_id = ba.id

    response = client.get(f'/api/bank_accounts/{ba_id}', headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()['name'] == "One Bank"


def test_update_bank_account(client, auth_headers, app):
    with app.app_context():
        account_id = Account.query.first().id
        ba = BankAccount(name="Old Name", account_number="OLD-001", account_id=account_id)
        db.session.add(ba)
        db.session.commit()
        ba_id = ba.id

    data = {"name": "New Name"}
    response = client.put(f'/api/bank_accounts/{ba_id}', json=data, headers=auth_headers)
    assert response.status_code == 200
    assert response.get_json()['name'] == "New Name"


def test_delete_bank_account(client, auth_headers, app):
    with app.app_context():
        account_id = Account.query.first().id
        ba = BankAccount(name="To Delete", account_number="DEL-001", account_id=account_id)
        db.session.add(ba)
        db.session.commit()
        ba_id = ba.id

    response = client.delete(f'/api/bank_accounts/{ba_id}', headers=auth_headers)
    assert response.status_code == 200

    response = client.get(f'/api/bank_accounts/{ba_id}', headers=auth_headers)
    assert response.status_code == 404
