from ..extensions import db
from .base import BaseModel

class Payment(db.Model, BaseModel):
    __tablename__ = 'payments'
    __table_args__ = (
        db.CheckConstraint('amount > 0', name='check_payment_amount_positive'),
    )
    
    date = db.Column(db.Date, nullable=False, index=True)
    amount = db.Column(db.Numeric(precision=20, scale=2), nullable=False)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False, index=True)
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=True, index=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=True, index=True)
    method = db.Column(db.String(50)) # e.g. Cash, Bank Transfer, Credit Card, Check
    
    # Relationships
    customer = db.relationship('Customer', backref='payments')
    invoice = db.relationship('Invoice', backref='payments')
    account = db.relationship('Account', backref='payments')

    def __repr__(self):
        return f'<Payment {self.id} - {self.amount}>'

class VendorPayment(db.Model, BaseModel):
    __tablename__ = 'vendor_payments'
    __table_args__ = (
        db.CheckConstraint('amount > 0', name='check_vendor_payment_amount_positive'),
    )
    
    date = db.Column(db.Date, nullable=False, index=True)
    amount = db.Column(db.Numeric(precision=20, scale=2), nullable=False)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False, index=True)
    bill_id = db.Column(db.Integer, db.ForeignKey('bills.id'), nullable=True, index=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=True, index=True)
    method = db.Column(db.String(50))
    
    # Relationships
    vendor = db.relationship('Vendor', backref='vendor_payments')
    bill = db.relationship('Bill', backref='vendor_payments')
    account = db.relationship('Account', backref='vendor_payments')

    def __repr__(self):
        return f'<VendorPayment {self.id} - {self.amount}>'
