import os
import sys
from datetime import date

# Add project root to sys.path if not there
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../'))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.app import create_app  # noqa: E402
from backend.extensions import db  # noqa: E402
from backend.seed import seed_data  # noqa: E402
from backend.models.settings import Settings  # noqa: E402
from backend.models.accounting_period import AccountingPeriod  # noqa: E402

def reset_database(interactive=True):
    """
    Resets the database to an initial empty state.
    1. Drops all tables.
    2. Recreates all tables.
    3. Seeds default chart of accounts.
    4. Seeds default business settings.
    5. Seeds current year accounting period.
    """
    if interactive:
        confirm = input("Are you sure you want to reset the database? ALL DATA WILL BE LOST! (y/N): ")
        if confirm.lower() != 'y':
            print("Reset cancelled.")
            return

    app = create_app()
    with app.app_context():
        print("Resetting database to initial state...")
        
        # SQLite specifically: drop all tables might be blocked by foreign keys if not handled
        # But drop_all() usually works fine with SQLite as long as there are no open transactions
        try:
            db.drop_all()
            print("All tables dropped.")
            
            db.create_all()
            print("Database schema recreated.")
        except Exception as e:
            print(f"Error during schema reset: {e}")
            return

        # Seed Chart of Accounts
        print("Seeding default chart of accounts...")
        seed_data(app)
        
        # Seed default business settings
        if not Settings.query.first():
            print("Seeding default settings...")
            default_settings = Settings(
                business_name="My Business",
                address="123 Business Way, Suite 100",
                default_currency="USD"
            )
            db.session.add(default_settings)
        
        # Seed default accounting period for current year
        current_year = date.today().year
        if not AccountingPeriod.query.filter_by(name=str(current_year)).first():
            print(f"Seeding default accounting period for {current_year}...")
            default_period = AccountingPeriod(
                name=str(current_year),
                start_date=date(current_year, 1, 1),
                end_date=date(current_year, 12, 31),
                is_closed=False
            )
            db.session.add(default_period)

        try:
            db.session.commit()
            print("Default data seeded successfully.")
        except Exception as e:
            db.session.rollback()
            print(f"Error seeding data: {e}")

        print("Database reset complete.")

if __name__ == "__main__":
    # If "--force" or "-f" is passed, run non-interactively
    force = "--force" in sys.argv or "-f" in sys.argv
    reset_database(interactive=not force)
