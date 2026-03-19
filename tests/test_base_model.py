import pytest
import time
from datetime import datetime
from flask import Flask
from backend.extensions import db
from backend.models.base import BaseModel

# A mock model for testing purposes
class MockModel(db.Model, BaseModel):
    __tablename__ = 'mock_model'
    name = db.Column(db.String(50))

@pytest.fixture
def app():
    """Create a Flask app instance for testing."""
    app = Flask(__name__)
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    db.init_app(app)
    
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()

def test_base_model_fields(app):
    """Verify that id, created_at, and updated_at are present and functional."""
    with app.app_context():
        # Test creation
        test_obj = MockModel(name="test_name")
        db.session.add(test_obj)
        db.session.commit()
        
        assert test_obj.id is not None
        assert test_obj.created_at is not None
        assert test_obj.updated_at is not None
        assert test_obj.name == "test_name"
        assert isinstance(test_obj.created_at, datetime)
        assert isinstance(test_obj.updated_at, datetime)

def test_base_model_serialization(app):
    """Verify the to_dict() method converts to a dictionary with ISO formatted dates."""
    with app.app_context():
        test_obj = MockModel(name="serialization_test")
        db.session.add(test_obj)
        db.session.commit()
        
        serialized_data = test_obj.to_dict()
        
        assert serialized_data['id'] == test_obj.id
        assert serialized_data['name'] == "serialization_test"
        assert 'created_at' in serialized_data
        assert 'updated_at' in serialized_data
        # Timestamps should be in string format (ISO 8601)
        assert isinstance(serialized_data['created_at'], str)
        assert isinstance(serialized_data['updated_at'], str)

def test_updated_at_automatic_update(app):
    """Verify that updated_at changes when the model is modified."""
    with app.app_context():
        # Create initial record
        test_obj = MockModel(name="initial_name")
        db.session.add(test_obj)
        db.session.commit()
        
        initial_updated_at = test_obj.updated_at
        
        # Sleep for a moment to ensure timestamp difference
        time.sleep(1.1)
        
        # Modify and commit
        test_obj.name = "updated_name"
        db.session.commit()
        
        # Fresh refresh to ensure updated_at is fetched from DB
        db.session.refresh(test_obj)
        
        assert test_obj.updated_at > initial_updated_at
