#!/usr/bin/env python3
import sys
import os
from sqlalchemy import create_engine, MetaData, text, inspect
from sqlalchemy.orm import sessionmaker

# Ensure project root is in sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.app import create_app
from backend.extensions import db
# Import all models to register them in metadata
from backend.models import *

def migrate_data():
    """
    Migrates data from SQLite to PostgreSQL.
    Assumes the Flask app is currently configured to use PostgreSQL (via environment variables).
    """
    app = create_app()
    with app.app_context():
        # Source SQLite database - explicitly defined as we assume we're moving from it
        sqlite_path = os.path.join(root_dir, 'data.sqlite')
        if not os.path.exists(sqlite_path):
            print(f"SQLite database not found at {sqlite_path}")
            return

        sqlite_uri = f"sqlite:///{sqlite_path}"
        sqlite_engine = create_engine(sqlite_uri)
        
        # Target PostgreSQL database (from Flask app config)
        pg_engine = db.engine
        
        # Check if the target is indeed PostgreSQL
        if 'postgresql' not in str(pg_engine.url):
            print("Error: Target database is not PostgreSQL.")
            print(f"Current URI: {pg_engine.url}")
            print("Please set your PostgreSQL environment variables in .env before running this script.")
            return

        print(f"Migrating data from {sqlite_uri} to {pg_engine.url}...")

        # Reflect alembic_version from SQLite if it exists
        sqlite_inspector = inspect(sqlite_engine)
        if 'alembic_version' in sqlite_inspector.get_table_names():
            print("Found alembic_version in SQLite, including in migration...")
            # Reflect it into db.metadata so it is included in db.create_all() and sorted_tables
            db.metadata.reflect(bind=sqlite_engine, only=['alembic_version'])

        # 1. Create all tables in PostgreSQL if they don't exist
        print("Ensuring target schema exists...")
        db.create_all()

        # 2. Get sorted tables to respect foreign key constraints
        sorted_tables = db.metadata.sorted_tables

        # Connect to both databases
        with sqlite_engine.connect() as sqlite_conn, pg_engine.connect() as pg_conn:
            # We use a transaction for Postgres to be safe
            pg_trans = pg_conn.begin()
            try:
                # 1. Clear existing data in reverse order to respect foreign keys
                print("Clearing existing data in target database...")
                for table in reversed(sorted_tables):
                    print(f"  Clearing {table.name}...")
                    pg_conn.execute(table.delete())

                # 2. Copy data in forward order
                for table in sorted_tables:
                    print(f"Migrating table: {table.name}...", end=" ", flush=True)
                    
                    # Fetch data from SQLite
                    rows = sqlite_conn.execute(table.select()).fetchall()
                    if not rows:
                        print("Empty (skipped)")
                        continue
                    
                    # Prepare data for insertion (convert rows to dicts)
                    data = [dict(row._mapping) for row in rows]
                    
                    # Insert data into PostgreSQL
                    pg_conn.execute(table.insert(), data)
                    print(f"Copied {len(data)} rows.")

                # 3. Update sequences for PostgreSQL
                print("Updating PostgreSQL sequences...")
                for table in sorted_tables:
                    # Check if table has an 'id' column
                    if 'id' in table.columns:
                        try:
                            # We use a more generic way to find the sequence name if possible, 
                            # but pg_get_serial_sequence('table', 'column') is standard for SERIAL
                            pg_conn.execute(text(f"""
                                SELECT setval(pg_get_serial_sequence('{table.name}', 'id'), 
                                       COALESCE((SELECT MAX(id) FROM {table.name}), 0) + 1, 
                                       false);
                            """))
                        except Exception as e:
                            # If it's not a serial column or sequence doesn't exist, just skip
                            pass

                pg_trans.commit()
                print("\nMigration completed successfully!")
                
            except Exception as e:
                pg_trans.rollback()
                print(f"\nMigration failed: {e}")
                raise e

if __name__ == "__main__":
    confirm = input("This will migrate all data from 'data.sqlite' to PostgreSQL. Existing data in PG will be overwritten. Continue? (y/N): ")
    if confirm.lower() == 'y':
        migrate_data()
    else:
        print("Migration cancelled.")
