import pytest
from backend.app import create_app
from backend.config import Config
from backend.extensions import db
from backend.models.item import Item
from backend.models.account import Account
from backend.models.tax import Tax
from flask_jwt_extended import create_access_token
from decimal import Decimal

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
    with client.application.app_context():
        token = create_access_token(identity='test-user')
        return {'Authorization': f'Bearer {token}'}

def test_item_api(client, auth_headers):
    with client.application.app_context():
        # Setup accounts and taxes
        income_acc = Account(name='Sales', code='4000', type='Revenue')
        expense_acc = Account(name='COGS', code='5000', type='Expense')
        tax = Tax(name='VAT', rate=Decimal('0.15'))
        db.session.add_all([income_acc, expense_acc, tax])
        db.session.commit()
        income_id = income_acc.id
        expense_id = expense_acc.id
        tax_id = tax.id

    # Create Item
    response = client.post('/api/items', json={
        'name': 'Widget',
        'description': 'A shiny widget',
        'price': '100.00',
        'sellable': True,
        'income_account_id': income_id,
        'purchaseable': True,
        'expense_account_id': expense_id,
        'sales_tax_ids': [tax_id]
    }, headers=auth_headers)
    
    assert response.status_code == 201
    assert response.json['name'] == 'Widget'
    assert response.json['price'] == '100.00'
    assert len(response.json['sales_taxes']) == 1
    item_id = response.json['id']

    # Get Item
    response = client.get(f'/api/items/{item_id}', headers=auth_headers)
    assert response.status_code == 200
    assert response.json['name'] == 'Widget'

    # Get List
    response = client.get('/api/items', headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json['items']) == 1

    # Update Item
    response = client.put(f'/api/items/{item_id}', json={
        'price': '120.00'
    }, headers=auth_headers)
    assert response.status_code == 200
    assert response.json['price'] == '120.00'

    # Delete Item
    response = client.delete(f'/api/items/{item_id}', headers=auth_headers)
    assert response.status_code == 200
    
    response = client.get('/api/items', headers=auth_headers)
    assert len(response.json['items']) == 0

def test_item_prefill_logic(client, auth_headers):
    from backend.models.invoice import Invoice, InvoiceLine
    from backend.models.customer import Customer
    
    with client.application.app_context():
        # Setup
        income_acc = Account(name='Sales', code='4000', type='Revenue')
        tax = Tax(name='VAT', rate=Decimal('0.10'))
        item = Item(
            name='Service', 
            description='Consulting', 
            price=Decimal('500.00'),
            income_account=income_acc,
            sales_taxes=[tax]
        )
        customer = Customer(name='Test Client')
        db.session.add_all([income_acc, tax, item, customer])
        db.session.commit()
        
        # Create Invoice Line with item_id but empty fields
        invoice = Invoice(customer_id=customer.id, issue_date=Decimal('0'), due_date=Decimal('0')) # simplified for logic test
        # Need real dates for Invoice model constraints if enforced
        from datetime import date
        invoice.issue_date = date.today()
        invoice.due_date = date.today()
        invoice.invoice_number = "INV-TEST"
        
        line = InvoiceLine(invoice=invoice, item_id=item.id, quantity=1, account_id=income_acc.id) # account_id is required by schema/model
        db.session.add(invoice)
        db.session.add(line)
        db.session.flush() # Should trigger before_flush pre-filling
        
        assert line.description == 'Consulting'
        assert float(line.unit_price) == 500.00
        assert len(line.taxes) == 1
        assert line.taxes[0].name == 'VAT'
