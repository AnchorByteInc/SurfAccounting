import pytest
from datetime import date
from decimal import Decimal
from backend.app import create_app
from backend.config import Config
from backend.extensions import db
from backend.models.account import Account
from backend.models.journal import JournalEntry, JournalEntryLine


class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        # Seed accounts
        a1 = Account(name="Cash", code="1000", type="Asset")
        a2 = Account(name="Revenue", code="4000", type="Revenue")
        db.session.add_all([a1, a2])
        db.session.commit()
        # Create a balanced entry to attach lines to
        entry = JournalEntry(date=date.today())
        entry.lines = [
            JournalEntryLine(account_id=a1.id, debit=Decimal('10.00')),
            JournalEntryLine(account_id=a2.id, credit=Decimal('10.00'))
        ]
        db.session.add(entry)
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
        entry = JournalEntry.query.first()
        a1 = Account.query.filter_by(code="1000").first()
        a2 = Account.query.filter_by(code="4000").first()
        return {"entry_id": entry.id, "debit_account_id": a1.id, "credit_account_id": a2.id}


def test_create_journal_entry_line(client, auth_headers, setup_data):
    # Create an extra debit line and a credit line to keep separate tests independent
    data = {
        "journal_entry_id": setup_data["entry_id"],
        "account_id": setup_data["debit_account_id"],
        "debit": "5.00"
    }
    response = client.post('/api/journal_entry_lines', json=data, headers=auth_headers)
    assert response.status_code == 201


def test_get_journal_entry_lines_pagination_and_filtering(client, auth_headers, setup_data, app):
    with app.app_context():
        # Add 15 lines to the same entry
        for i in range(15):
            db.session.add(JournalEntryLine(
                journal_entry_id=setup_data["entry_id"],
                account_id=setup_data["debit_account_id"],
                debit=Decimal('1.00')
            ))
        db.session.commit()

    # Page 1
    response = client.get(f'/api/journal_entry_lines?page=1&per_page=10&journal_entry_id={setup_data["entry_id"]}', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['journal_entry_lines']) == 10
    assert json_data['total'] >= 15

    # Filter by type
    response = client.get('/api/journal_entry_lines?type=debit', headers=auth_headers)
    assert response.status_code == 200


def test_get_single_update_delete_journal_entry_line(client, auth_headers, setup_data, app):
    with app.app_context():
        line = JournalEntryLine(
            journal_entry_id=setup_data["entry_id"],
            account_id=setup_data["debit_account_id"],
            debit=Decimal('2.00')
        )
        db.session.add(line)
        db.session.commit()
        line_id = line.id

    # Get
    response = client.get(f'/api/journal_entry_lines/{line_id}', headers=auth_headers)
    assert response.status_code == 200

    # Update: switch to credit should be rejected by schema if both provided; we'll just change amount value
    response = client.put(f'/api/journal_entry_lines/{line_id}', json={"debit": "3.00"}, headers=auth_headers)
    assert response.status_code == 200

    # Delete
    response = client.delete(f'/api/journal_entry_lines/{line_id}', headers=auth_headers)
    assert response.status_code == 200

    # Ensure gone
    response = client.get(f'/api/journal_entry_lines/{line_id}', headers=auth_headers)
    assert response.status_code == 404


def test_create_journal_line_invalid_account(client, auth_headers, setup_data):
    data = {
        "journal_entry_id": setup_data["entry_id"],
        "account_id": 999999,
        "debit": "1.00"
    }
    response = client.post('/api/journal_entry_lines', json=data, headers=auth_headers)
    assert response.status_code == 400
