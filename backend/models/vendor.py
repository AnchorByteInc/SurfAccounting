from ..extensions import db
from .base import BaseModel

class Vendor(db.Model, BaseModel):
    __tablename__ = 'vendors'
    
    name = db.Column(db.String(100), nullable=False)
    primary_contact_name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=True)
    phone = db.Column(db.String(20), nullable=True)
    address = db.Column(db.Text, nullable=True)
    balance = db.Column(db.Numeric(precision=20, scale=2), default=0.0)
    
    def __repr__(self):
        return f'<Vendor {self.name}>'
