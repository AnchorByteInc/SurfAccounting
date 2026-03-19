from ..extensions import db
from .base import BaseModel

class Customer(db.Model, BaseModel):
    __tablename__ = 'customers'
    
    name = db.Column(db.String(100), nullable=False)
    primary_contact_name = db.Column(db.String(100), nullable=True)
    email = db.Column(db.String(100), unique=True, nullable=True) # 2.2.5 Validation: unique email
    phone = db.Column(db.String(20), nullable=True)
    website = db.Column(db.String(255), nullable=True)
    billing_address = db.Column(db.Text, nullable=True)
    shipping_address = db.Column(db.Text, nullable=True)
    balance = db.Column(db.Numeric(precision=20, scale=2), default=0.0)
    
    def __repr__(self):
        return f'<Customer {self.name}>'
