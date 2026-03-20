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
from flask_migrate import upgrade as flask_migrate_upgrade

def reset_database(interactive=True):
    """
    Resets the database to an initial empty state.
    1. Drops all tables.
    2. Recreates all tables.
    3. Seeds default data.
    """
    if interactive:
        confirm = input("Are you sure you want to reset the database? ALL DATA WILL BE LOST! (y/N): ")
        if confirm.lower() != 'y':
            print("Reset cancelled.")
            return

    app = create_app()
    with app.app_context():
        print("Resetting database to initial state...")
        
        try:
            db.drop_all()
            print("All tables dropped.")
            
            # Using flask-migrate to upgrade the schema to the latest version
            # This is better than db.create_all() because it also initializes the alembic_version table
            flask_migrate_upgrade()
            print("Database schema recreated via migrations.")
        except Exception as e:
            print(f"Error during schema reset: {e}")
            return

        seed_only_logic(app)
        print("Database reset complete.")

def seed_only_logic(app):
    """
    Seeds the database with default data if not already present.
    """
    with app.app_context():
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

def seed_database():
    app = create_app()
    seed_only_logic(app)

if __name__ == "__main__":
    # If "--force" or "-f" is passed, run non-interactively
    force = "--force" in sys.argv or "-f" in sys.argv
    reset_database(interactive=not force)
