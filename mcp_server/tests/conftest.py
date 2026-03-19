import pytest
import os
import sys

# Add the project root to sys.path
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from flask import Flask
from backend.extensions import db
from backend.config import Config
import mcp_server.utils.db

class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True

@pytest.fixture(scope='session', autouse=True)
def setup_test_app():
    # Create a test app
    test_app = mcp_server.utils.db.create_app(TestConfig)
    
    # Patch the app in mcp_server.utils.db
    original_app = mcp_server.utils.db.app
    mcp_server.utils.db.app = test_app
    
    # Import all models to ensure they are registered with SQLAlchemy
    from backend import models
    
    with test_app.app_context():
        db.create_all()
        yield test_app
        db.drop_all()
    
    # Restore the original app (though probably not necessary for tests)
    mcp_server.utils.db.app = original_app

@pytest.fixture(autouse=True)
def clean_db(setup_test_app):
    """
    Clear data between tests.
    """
    with setup_test_app.app_context():
        # Using clear_data instead of drop/create to be faster if possible, 
        # but for simplicity now just truncate tables or rely on rollback if we use transactions.
        # Since we use commit in get_db_session, we might need to manually delete.
        db.session.rollback()
        for table in reversed(db.metadata.sorted_tables):
            db.session.execute(table.delete())
        db.session.commit()
        db.session.remove()
