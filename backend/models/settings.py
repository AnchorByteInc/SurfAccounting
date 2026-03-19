from ..extensions import db
from .base import BaseModel

class Settings(db.Model, BaseModel):
    __tablename__ = 'settings'
    
    business_name = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text)
    city = db.Column(db.String(100))
    state = db.Column(db.String(100))
    zip = db.Column(db.String(20))
    email = db.Column(db.String(100))
    default_currency = db.Column(db.String(3), default='USD')
    app_logo_url = db.Column(db.String(255))
    invoice_logo_url = db.Column(db.String(255))

    def __repr__(self):
        return f'<Settings {self.business_name}>'
