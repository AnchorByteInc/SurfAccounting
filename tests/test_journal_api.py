import pytest
from datetime import date, timedelta
from decimal import Decimal
from backend.app import create_app
from backend.config import Config
from backend.extensions import db
from backend.models.account import Account
from backend.models.journal import JournalEntry


class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        # Seed accounts used by journal lines
        db.session.add(Account(name="Cash", code="1000", type="Asset"))
        db.session.add(Account(name="Revenue", code="4000", type="Revenue"))
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


def get_account_ids(app):
    with app.app_context():
        accounts = Account.query.order_by(Account.code).all()
        return accounts[0].id, accounts[1].id


def test_create_journal_entry(client, auth_headers, app):
    debit_acct_id, credit_acct_id = get_account_ids(app)

    data = {
        "date": date.today().isoformat(),
        "memo": "Test entry",
        "reference": "JE-001",
        "lines": [
            {"account_id": debit_acct_id, "debit": "100.00"},
            {"account_id": credit_acct_id, "credit": "100.00"}
        ]
    }

    response = client.post('/api/journal_entries', json=data, headers=auth_headers)
    if response.status_code != 201:
        print(response.get_json())
    assert response.status_code == 201
    json_data = response.get_json()
    assert json_data['reference'] == "JE-001"
    assert len(json_data['lines']) == 2


def test_create_unbalanced_journal_entry(client, auth_headers, app):
    debit_acct_id, credit_acct_id = get_account_ids(app)

    data = {
        "date": date.today().isoformat(),
        "memo": "Unbalanced",
        "reference": "JE-UB",
        "lines": [
            {"account_id": debit_acct_id, "debit": "100.00"},
            {"account_id": credit_acct_id, "credit": "50.00"}
        ]
    }

    response = client.post('/api/journal_entries', json=data, headers=auth_headers)
    assert response.status_code == 400
    assert 'message' in response.get_json()


def test_get_journal_entries_pagination_and_filtering(client, auth_headers, app):
    with app.app_context():
        a1, a2 = get_account_ids(app)
        # Create 15 entries alternating memo/reference and dates
        base_date = date.today()
        for i in range(15):
            je = JournalEntry(date=base_date - timedelta(days=i), memo=f"Memo {i}", reference=f"JE-{i:03d}")
            from backend.models.journal import JournalEntryLine
            je.lines = [
                JournalEntryLine(account_id=a1, debit=Decimal('10.00')),
                JournalEntryLine(account_id=a2, credit=Decimal('10.00'))
            ]
            db.session.add(je)
        db.session.commit()

    # Page 1
    response = client.get('/api/journal_entries?page=1&per_page=10', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['journal_entries']) == 10
    assert json_data['total'] == 15

    # Filter by reference
    response = client.get('/api/journal_entries?reference=JE-005', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['journal_entries']) == 1
    assert json_data['journal_entries'][0]['reference'] == 'JE-005'


def test_update_and_delete_journal_entry(client, auth_headers, app):
    debit_acct_id, credit_acct_id = get_account_ids(app)

    # Create entry first
    create_resp = client.post('/api/journal_entries', json={
        "date": date.today().isoformat(),
        "memo": "To Update",
        "reference": "JE-UPD",
        "lines": [
            {"account_id": debit_acct_id, "debit": "50.00"},
            {"account_id": credit_acct_id, "credit": "50.00"}
        ]
    }, headers=auth_headers)
    assert create_resp.status_code == 201
    entry_id = create_resp.get_json()['id']

    # Update memo
    upd_resp = client.put(f'/api/journal_entries/{entry_id}', json={"memo": "Updated Memo"}, headers=auth_headers)
    assert upd_resp.status_code == 200
    assert upd_resp.get_json()['memo'] == "Updated Memo"

    # Delete
    del_resp = client.delete(f'/api/journal_entries/{entry_id}', headers=auth_headers)
    assert del_resp.status_code == 200

    # Ensure gone
    get_resp = client.get(f'/api/journal_entries/{entry_id}', headers=auth_headers)
    assert get_resp.status_code == 404
