from ..extensions import db
from .base import BaseModel

class Account(db.Model, BaseModel):
    __tablename__ = 'accounts'
    
    name = db.Column(db.String(100), nullable=False)
    code = db.Column(db.String(20), unique=True, nullable=False) # 2.2.2
    type = db.Column(db.String(50), nullable=False) # e.g. Asset, Liability, Equity, Revenue, Expense
    subtype = db.Column(db.String(50)) # e.g. Bank, Accounts Receivable, etc.
    parent_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    is_system = db.Column(db.Boolean, default=False)
    
    # 2.2.3 Relationship for parent/child accounts
    parent = db.relationship('Account', remote_side='Account.id', backref='children')

    def __repr__(self):
        return f'<Account {self.code} - {self.name}>'
