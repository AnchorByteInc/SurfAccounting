import pytest
from backend.app import create_app
from backend.config import Config
from backend.extensions import db
from backend.models.vendor import Vendor
from backend.models.bill import Bill
from datetime import date, timedelta


class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True


@pytest.fixture
def app():
    app = create_app(TestConfig)
    with app.app_context():
        db.create_all()
        # Seed a vendor
        vend = Vendor(name="Acme Corp", email="acme@example.com")
        db.session.add(vend)
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


def test_create_vendor_payment(client, auth_headers, app):
    with app.app_context():
        vendor_id = Vendor.query.first().id
    data = {
        "date": date.today().isoformat(),
        "amount": 250.00,
        "vendor_id": vendor_id,
        "method": "Wire"
    }
    response = client.post('/api/vendor_payments', json=data, headers=auth_headers)
    assert response.status_code == 201
    json_data = response.get_json()
    assert float(json_data['amount']) == 250.00
    assert json_data['vendor_id'] == vendor_id


def test_get_vendor_payments_pagination_and_filtering(client, auth_headers, app):
    with app.app_context():
        vend = Vendor.query.first()
        # Create a bill to use for filter
        bill = Bill(
            vendor_id=vend.id,
            bill_number="BILL-PAY-001",
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            status='draft'
        )
        db.session.add(bill)
        db.session.flush()
        # Create 15 vendor payments alternating method and bill link
        for i in range(15):
            payload = {
                "date": date.today().isoformat(),
                "amount": float(20 + i),
                "vendor_id": vend.id,
                "bill_id": bill.id if i % 2 == 0 else None,
                "method": "Check" if i % 2 == 0 else "ACH"
            }
            client.post('/api/vendor_payments', json=payload, headers=auth_headers)
        db.session.commit()

    # Page 1
    response = client.get('/api/vendor_payments?page=1&per_page=10', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['vendor_payments']) == 10
    assert json_data['total'] >= 15

    # Filter by method
    response = client.get('/api/vendor_payments?method=Check', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert all('Check' in (p['method'] or '') for p in json_data['vendor_payments'])

    # Filter by bill_id
    with app.app_context():
        bill_id = Bill.query.filter_by(bill_number="BILL-PAY-001").first().id
    response = client.get(f'/api/vendor_payments?bill_id={bill_id}', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert all(p['bill_id'] == bill_id for p in json_data['vendor_payments'])


def test_update_and_delete_vendor_payment(client, auth_headers, app):
    with app.app_context():
        vendor_id = Vendor.query.first().id
    # Create
    data = {
        "date": date.today().isoformat(),
        "amount": 75.0,
        "vendor_id": vendor_id,
        "method": "ACH"
    }
    create_resp = client.post('/api/vendor_payments', json=data, headers=auth_headers)
    assert create_resp.status_code == 201
    pid = create_resp.get_json()['id']

    # Update
    upd_resp = client.put(f'/api/vendor_payments/{pid}', json={"method": "Check"}, headers=auth_headers)
    assert upd_resp.status_code == 200
    assert upd_resp.get_json()['method'] == "Check"

    # Delete
    del_resp = client.delete(f'/api/vendor_payments/{pid}', headers=auth_headers)
    assert del_resp.status_code == 200
    get_resp = client.get(f'/api/vendor_payments/{pid}', headers=auth_headers)
    assert get_resp.status_code == 404


def test_create_vendor_payment_validation_errors(client, auth_headers):
    # Missing date
    resp = client.post('/api/vendor_payments', json={
        "amount": 10.0,
        "vendor_id": 1
    }, headers=auth_headers)
    assert resp.status_code == 400
    assert 'date' in resp.get_json()

    # Negative amount
    resp = client.post('/api/vendor_payments', json={
        "date": date.today().isoformat(),
        "amount": -10.0,
        "vendor_id": 1
    }, headers=auth_headers)
    assert resp.status_code == 400
    assert 'amount' in resp.get_json()

    # Invalid vendor
    resp = client.post('/api/vendor_payments', json={
        "date": date.today().isoformat(),
        "amount": 10.0,
        "vendor_id": 999999
    }, headers=auth_headers)
    assert resp.status_code == 400
    assert 'vendor_id' in resp.get_json()
