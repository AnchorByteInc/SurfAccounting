from datetime import datetime
from backend.extensions import db

class BaseModel:
    """
    A base model mixin that includes id, created_at, and updated_at fields
    along with a reusable serialization method.
    """
    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    created_at = db.Column(db.DateTime, server_default=db.func.now())
    updated_at = db.Column(db.DateTime, server_default=db.func.now(), onupdate=db.func.now())

    def to_dict(self):
        """
        Generic serialization method that converts the model instance into a dictionary.
        Handles datetime objects by converting them into ISO format.
        """
        data = {}
        # We use __table__.columns to iterate over columns defined in the model
        for column in self.__table__.columns:
            value = getattr(self, column.name)
            # Check if the value is a datetime object and format it accordingly
            if isinstance(value, datetime):
                data[column.name] = value.isoformat() if value else None
            else:
                data[column.name] = value
        return data
