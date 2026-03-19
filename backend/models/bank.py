from ..extensions import db
from .base import BaseModel

class BankAccount(db.Model, BaseModel):
    __tablename__ = 'bank_accounts'
    
    name = db.Column(db.String(100), nullable=False)
    account_number = db.Column(db.String(50))
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False) # The ledger account
    
    # Relationships
    account = db.relationship('Account', backref='bank_account')

    def __repr__(self):
        return f'<BankAccount {self.name}>'

class BankReconciliation(db.Model, BaseModel):
    __tablename__ = 'bank_reconciliations'
    
    bank_account_id = db.Column(db.Integer, db.ForeignKey('bank_accounts.id'), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    ending_balance = db.Column(db.Numeric(precision=20, scale=2), default=0.0)
    status = db.Column(db.String(20), default='draft') # draft, completed
    
    # Relationships
    bank_account = db.relationship('BankAccount', backref='reconciliations')

    def __repr__(self):
        return f'<BankReconciliation {self.id} for {self.bank_account_id}>'
