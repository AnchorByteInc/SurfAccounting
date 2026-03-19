from ..extensions import db
from .base import BaseModel

# Association table for InvoiceLine and Tax
invoice_line_taxes = db.Table('invoice_line_taxes',
    db.Column('invoice_line_id', db.Integer, db.ForeignKey('invoice_lines.id'), primary_key=True),
    db.Column('tax_id', db.Integer, db.ForeignKey('taxes.id'), primary_key=True)
)

# Association table for BillLine and Tax
bill_line_taxes = db.Table('bill_line_taxes',
    db.Column('bill_line_id', db.Integer, db.ForeignKey('bill_lines.id'), primary_key=True),
    db.Column('tax_id', db.Integer, db.ForeignKey('taxes.id'), primary_key=True)
)

class Tax(db.Model, BaseModel):
    __tablename__ = 'taxes'
    
    name = db.Column(db.String(100), nullable=False)
    rate = db.Column(db.Numeric(precision=10, scale=4), nullable=False) # e.g. 0.0700 for 7%
    description = db.Column(db.String(255))
    is_active = db.Column(db.Boolean, default=True)

    # Accounts for GL transactions
    asset_account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=True) # Used for billing
    liability_account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=True) # Used for invoicing

    # Relationships
    asset_account = db.relationship('Account', foreign_keys=[asset_account_id], backref='tax_assets')
    liability_account = db.relationship('Account', foreign_keys=[liability_account_id], backref='tax_liabilities')

    def __repr__(self):
        return f'<Tax {self.name} ({self.rate * 100}%)>'
