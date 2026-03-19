import pytest
from backend.app import create_app
from backend.config import Config
from backend.extensions import db
from backend.models.account import Account
from backend.models.tax import Tax
from flask_jwt_extended import create_access_token
from decimal import Decimal

class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True
    JWT_SECRET_KEY = 'test-secret-at-least-32-bytes-long-for-security-purposes'

def test_reproduce_500():
    app = create_app(TestConfig)
    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            
            # Setup accounts and taxes
            income_acc = Account(id=10, name='Sales', code='4000', type='Revenue')
            expense_acc = Account(id=19, name='COGS', code='5000', type='Expense')
            tax = Tax(id=1, name='VAT', rate=Decimal('0.15'))
            db.session.add_all([income_acc, expense_acc, tax])
            db.session.commit()
            
            token = create_access_token(identity='test-user')
            headers = {'Authorization': f'Bearer {token}'}
            
            payload = {
                "name":"Test Item",
                "description":"Testing Item",
                "price":100,
                "sellable":True,
                "income_account_id":10,
                "purchaseable":True,
                "expense_account_id":19,
                "sales_tax_ids":[1]
            }
            
            response = client.post('/api/items', json=payload, headers=headers)
            
            print(f"Response status: {response.status_code}")
            print(f"Response body: {response.get_data(as_text=True)}")
            
            assert response.status_code == 201

if __name__ == "__main__":
    test_reproduce_500()
