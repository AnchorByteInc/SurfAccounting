import os
import sys

# Ensure the project root is in sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.app import create_app
from backend.extensions import db
from backend.models.account import Account
from backend.models.user import User

def seed_data(app=None):
    if app is None:
        app = create_app()
    
    with app.app_context():
        # Seed Admin User if not exists
        if not User.query.filter_by(username='admin').first():
            print("Seeding default admin user...")
            admin = User(
                username='admin',
                email='admin@example.com',
                is_admin=True
            )
            admin.set_password('admin123')
            db.session.add(admin)

        # Check if accounts already exist
        if Account.query.first():
            print("Database already seeded.")
            return

        print("Seeding default accounts...")

        accounts = [
            # ASSETS
            {'name': 'Cash', 'code': '1000', 'type': 'Asset', 'subtype': 'Bank'},
            {'name': 'Accounts Receivable', 'code': '1200', 'type': 'Asset', 'subtype': 'Accounts Receivable'},
            {'name': 'Inventory', 'code': '1400', 'type': 'Asset', 'subtype': 'Current Asset'},
            {'name': 'Prepaid Expenses', 'code': '1600', 'type': 'Asset', 'subtype': 'Current Asset'},
            
            # LIABILITIES
            {'name': 'Accounts Payable', 'code': '2000', 'type': 'Liability', 'subtype': 'Accounts Payable'},
            {'name': 'Sales Tax Payable', 'code': '2200', 'type': 'Liability', 'subtype': 'Current Liability'},
            {'name': 'Credit Card', 'code': '2300', 'type': 'Liability', 'subtype': 'Credit Card'},
            
            # EQUITY
            {'name': 'Owner\'s Equity', 'code': '3000', 'type': 'Equity', 'subtype': 'Equity'},
            {'name': 'Retained Earnings', 'code': '3100', 'type': 'Equity', 'subtype': 'Equity'},
            
            # REVENUE
            {'name': 'Sales', 'code': '4000', 'type': 'Revenue', 'subtype': 'Revenue'},
            {'name': 'Service Revenue', 'code': '4100', 'type': 'Revenue', 'subtype': 'Revenue'},
            {'name': 'Other Income', 'code': '4200', 'type': 'Revenue', 'subtype': 'Revenue'},
            
            # EXPENSES
            {'name': 'Cost of Goods Sold', 'code': '5000', 'type': 'Expense', 'subtype': 'Cost of Goods Sold'},
            {'name': 'Advertising', 'code': '5100', 'type': 'Expense', 'subtype': 'Operating Expense'},
            {'name': 'Bank Fees', 'code': '5200', 'type': 'Expense', 'subtype': 'Operating Expense'},
            {'name': 'Rent', 'code': '5300', 'type': 'Expense', 'subtype': 'Operating Expense'},
            {'name': 'Salaries and Wages', 'code': '5400', 'type': 'Expense', 'subtype': 'Operating Expense'},
            {'name': 'Utilities', 'code': '5500', 'type': 'Expense', 'subtype': 'Operating Expense'},
            {'name': 'General Expenses', 'code': '5600', 'type': 'Expense', 'subtype': 'Operating Expense'},
        ]

        for acc_data in accounts:
            account = Account(
                name=acc_data['name'],
                code=acc_data['code'],
                type=acc_data['type'],
                subtype=acc_data['subtype']
            )
            db.session.add(account)

        try:
            db.session.commit()
            print("Successfully seeded Chart of Accounts.")
        except Exception as e:
            db.session.rollback()
            print(f"Error seeding database: {e}")

if __name__ == "__main__":
    seed_data()
