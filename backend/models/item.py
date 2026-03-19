from ..extensions import db
from .base import BaseModel

# Association table for Item and Tax
item_taxes = db.Table('item_taxes',
    db.Column('item_id', db.Integer, db.ForeignKey('items.id'), primary_key=True),
    db.Column('tax_id', db.Integer, db.ForeignKey('taxes.id'), primary_key=True)
)

class Item(db.Model, BaseModel):
    __tablename__ = 'items'

    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    price = db.Column(db.Numeric(precision=20, scale=2), default=0.0)
    
    sellable = db.Column(db.Boolean, default=True)
    income_account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=True)
    
    purchaseable = db.Column(db.Boolean, default=False)
    expense_account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=True)

    # Relationships
    income_account = db.relationship('Account', foreign_keys=[income_account_id], backref='items_as_income')
    expense_account = db.relationship('Account', foreign_keys=[expense_account_id], backref='items_as_expense')
    sales_taxes = db.relationship('Tax', secondary=item_taxes, backref='items')

    def __repr__(self):
        return f'<Item {self.name}>'
