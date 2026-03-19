from ..extensions import db
from .base import BaseModel

class Transaction(db.Model, BaseModel):
    __tablename__ = 'transactions'
    
    date = db.Column(db.Date, nullable=False)
    description = db.Column(db.String(255))
    reference_type = db.Column(db.String(50)) # e.g. 'invoice', 'bill', 'payment'
    reference_id = db.Column(db.Integer)
    
    # Relationships
    details = db.relationship('TransactionDetail', backref='transaction', cascade='all, delete-orphan')

    def __repr__(self):
        return f'<Transaction {self.id} - {self.description}>'

class TransactionDetail(db.Model, BaseModel):
    __tablename__ = 'transaction_details'
    
    transaction_id = db.Column(db.Integer, db.ForeignKey('transactions.id'), nullable=False)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    debit = db.Column(db.Numeric(precision=20, scale=2), default=0.0)
    credit = db.Column(db.Numeric(precision=20, scale=2), default=0.0)
    
    # Relationships
    account = db.relationship('Account', backref='transaction_details')

    def __repr__(self):
        return f'<TransactionDetail {self.id}: Account {self.account_id} D:{self.debit} C:{self.credit}>'
