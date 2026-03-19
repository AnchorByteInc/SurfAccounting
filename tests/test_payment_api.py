import pytest
from backend.app import create_app
from backend.config import Config
from backend.extensions import db
from backend.models.customer import Customer
from backend.models.invoice import Invoice
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
        # Seed a customer
        cust = Customer(name="Alice", email="alice@example.com")
        db.session.add(cust)
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


def test_create_payment(client, auth_headers, app):
    with app.app_context():
        customer_id = Customer.query.first().id
    data = {
        "date": date.today().isoformat(),
        "amount": 150.00,
        "customer_id": customer_id,
        "method": "Bank Transfer"
    }
    response = client.post('/api/payments', json=data, headers=auth_headers)
    assert response.status_code == 201
    json_data = response.get_json()
    assert float(json_data['amount']) == 150.00
    assert json_data['customer_id'] == customer_id


def test_get_payments_pagination_and_filtering(client, auth_headers, app):
    with app.app_context():
        cust = Customer.query.first()
        # Create an invoice to use for filter
        inv = Invoice(
            customer_id=cust.id,
            invoice_number="INV-PAY-001",
            issue_date=date.today(),
            due_date=date.today() + timedelta(days=30),
            status='draft'
        )
        db.session.add(inv)
        db.session.flush()
        # Create 15 payments, alternating method and invoice link
        for i in range(15):
            p = {
                "date": date.today(),
                "amount": 10 + i,
                "customer_id": cust.id,
                "invoice_id": inv.id if i % 2 == 0 else None,
                "method": "Cash" if i % 2 == 0 else "Card"
            }
            # Use API for creation to ensure validation path works
            client.post('/api/payments', json={
                "date": p["date"].isoformat(),
                "amount": float(p["amount"]),
                "customer_id": p["customer_id"],
                "invoice_id": p["invoice_id"],
                "method": p["method"]
            }, headers=auth_headers)
        db.session.commit()

    # Page 1
    response = client.get('/api/payments?page=1&per_page=10', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert len(json_data['payments']) == 10
    assert json_data['total'] >= 15

    # Filter by method
    response = client.get('/api/payments?method=Cash', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert all('Cash' in (p['method'] or '') for p in json_data['payments'])

    # Filter by invoice_id
    with app.app_context():
        inv_id = Invoice.query.filter_by(invoice_number="INV-PAY-001").first().id
    response = client.get(f'/api/payments?invoice_id={inv_id}', headers=auth_headers)
    assert response.status_code == 200
    json_data = response.get_json()
    assert all(p['invoice_id'] == inv_id for p in json_data['payments'])


def test_update_and_delete_payment(client, auth_headers, app):
    with app.app_context():
        cust_id = Customer.query.first().id
    # Create
    data = {
        "date": date.today().isoformat(),
        "amount": 50.0,
        "customer_id": cust_id,
        "method": "Cash"
    }
    create_resp = client.post('/api/payments', json=data, headers=auth_headers)
    assert create_resp.status_code == 201
    pid = create_resp.get_json()['id']

    # Update
    upd_resp = client.put(f'/api/payments/{pid}', json={"method": "Card"}, headers=auth_headers)
    assert upd_resp.status_code == 200
    assert upd_resp.get_json()['method'] == "Card"

    # Delete
    del_resp = client.delete(f'/api/payments/{pid}', headers=auth_headers)
    assert del_resp.status_code == 200
    get_resp = client.get(f'/api/payments/{pid}', headers=auth_headers)
    assert get_resp.status_code == 404


def test_create_payment_validation_errors(client, auth_headers, app):
    with app.app_context():
        cust_id = Customer.query.first().id
    # Missing date
    resp = client.post('/api/payments', json={
        "amount": 10.0,
        "customer_id": cust_id
    }, headers=auth_headers)
    assert resp.status_code == 400
    assert 'date' in resp.get_json()

    # Negative amount
    resp = client.post('/api/payments', json={
        "date": date.today().isoformat(),
        "amount": -5.0,
        "customer_id": cust_id
    }, headers=auth_headers)
    assert resp.status_code == 400
    assert 'amount' in resp.get_json()

    # Invalid customer
    resp = client.post('/api/payments', json={
        "date": date.today().isoformat(),
        "amount": 10.0,
        "customer_id": 999999
    }, headers=auth_headers)
    assert resp.status_code == 400
    assert 'customer_id' in resp.get_json()
