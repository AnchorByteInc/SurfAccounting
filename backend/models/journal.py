from sqlalchemy import event
from ..extensions import db
from .base import BaseModel
from ..utils.money import to_decimal

class JournalEntry(db.Model, BaseModel):
    __tablename__ = 'journal_entries'
    
    date = db.Column(db.Date, nullable=False, index=True)
    memo = db.Column(db.String(255))
    reference = db.Column(db.String(100))
    
    # New metadata columns
    transaction_type = db.Column(db.String(50)) # e.g., Expense, Journal Entry, Transfer, Deposit, Invoice, Payment, Credit Card Payment
    source_module = db.Column(db.String(20))    # e.g., "INV", "BILL", "PAY"
    source_id = db.Column(db.Integer)           # ID of the source record (Invoice ID, Bill ID, Payment ID, etc.)
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=True)
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=True)

    # Relationships
    lines = db.relationship('JournalEntryLine', backref='journal_entry', cascade='all, delete-orphan')
    vendor = db.relationship('Vendor', backref='journal_entries')
    customer = db.relationship('Customer', backref='journal_entries')

    def is_balanced(self):
        """2.2.14 Enforce debit/credit balance validation method"""
        debits = sum(to_decimal(line.debit or 0) for line in self.lines)
        credits = sum(to_decimal(line.credit or 0) for line in self.lines)
        return debits == credits

    def __repr__(self):
        return f'<JournalEntry {self.id} - {self.date}>'

@event.listens_for(JournalEntry, 'before_insert')
@event.listens_for(JournalEntry, 'before_update')
def validate_journal_entry_balance(mapper, connection, target):
    """3.1.2 Prevent journal entry save if unbalanced"""
    if not target.is_balanced():
        debits = sum(to_decimal(line.debit or 0) for line in target.lines)
        credits = sum(to_decimal(line.credit or 0) for line in target.lines)
        raise ValueError(f"Journal entry is not balanced. Total Debits: {debits}, Total Credits: {credits}")

class JournalEntryLine(db.Model, BaseModel):
    __tablename__ = 'journal_entry_lines'
    __table_args__ = (
        db.CheckConstraint('debit >= 0', name='check_journal_line_debit_positive'),
        db.CheckConstraint('credit >= 0', name='check_journal_line_credit_positive'),
    )
    
    journal_entry_id = db.Column(db.Integer, db.ForeignKey('journal_entries.id'), nullable=False, index=True)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False, index=True)
    debit = db.Column(db.Numeric(precision=20, scale=2), default=0.0)
    credit = db.Column(db.Numeric(precision=20, scale=2), default=0.0)
    description = db.Column(db.Text)
    
    # Relationships
    account = db.relationship('Account', backref='journal_lines')

    def __repr__(self):
        return f'<JournalEntryLine {self.id}: Account {self.account_id} D:{self.debit} C:{self.credit}>'
