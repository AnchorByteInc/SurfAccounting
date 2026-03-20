from sqlalchemy import event
from decimal import Decimal
from ..extensions import db
from .base import BaseModel

class Bill(db.Model, BaseModel):
    __tablename__ = 'bills'
    __table_args__ = (
        db.CheckConstraint('total >= 0', name='check_bill_total_positive'),
        db.CheckConstraint('balance >= 0', name='check_bill_balance_positive'),
        db.CheckConstraint('due_date >= issue_date', name='check_bill_due_date_after_issue'),
    )
    
    vendor_id = db.Column(db.Integer, db.ForeignKey('vendors.id'), nullable=False, index=True)
    bill_number = db.Column(db.String(50), unique=True, nullable=False)
    issue_date = db.Column(db.Date, nullable=False, index=True)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='draft', index=True) # draft, approved, paid, overdue, cancelled
    subtotal = db.Column(db.Numeric(precision=20, scale=2), default=0.0)
    tax = db.Column(db.Numeric(precision=20, scale=2), default=0.0)
    total = db.Column(db.Numeric(precision=20, scale=2), default=0.0)
    balance = db.Column(db.Numeric(precision=20, scale=2), default=0.0)
    
    # Relationships
    vendor = db.relationship('Vendor', backref='bills')
    lines = db.relationship('BillLine', backref='bill', cascade='all, delete-orphan')

    def calculate_totals(self):
        """
        3.4.1 Calculate bill totals
        """
        # Include lines already in the collection and new ones in the session
        lines_to_sum = list(self.lines)
        for obj in db.session.new:
            if isinstance(obj, BillLine) and (obj.bill == self or (self.id and obj.bill_id == self.id)):
                if obj not in lines_to_sum:
                    lines_to_sum.append(obj)
                    
        # Exclude lines that are about to be deleted
        lines_to_sum = [line for line in lines_to_sum if line not in db.session.deleted]

        # Preserve existing total if there are no lines and a positive total is already set (non-draft)
        preserve_existing_totals = (len(lines_to_sum) == 0 and self.total and Decimal(str(self.total)) > 0 and self.status != 'draft')
        if not preserve_existing_totals:
            self.subtotal = sum(line.calculate_line_total() for line in lines_to_sum)
            self.tax = sum(line.calculate_tax_amount() for line in lines_to_sum)
            self.total = self.subtotal + self.tax
        
        # When in draft, the balance should stay in sync with the total if no payments exist.
        # Once it's open or paid, the balance is managed by payments (Phase 3.5)
        if self.status == 'cancelled':
            self.balance = Decimal('0.00')
        else:
            # Re-calculate balance based on payments
            with db.session.no_autoflush:
                from .payment import VendorPayment
                # Query payments from DB (includes flushed but not committed)
                if self.id:
                    payments = db.session.query(VendorPayment).filter_by(bill_id=self.id).all()
                else:
                    payments = []
                
                # Also check session.new for payments not yet flushed
                for obj in db.session.new:
                    if isinstance(obj, VendorPayment) and (obj.bill == self or (self.id and obj.bill_id == self.id)):
                        if obj not in payments:
                            payments.append(obj)
            
            total_paid = sum(p.amount for p in payments if p not in db.session.deleted)
            
            # Special case: a bill marked as 'paid' with no recorded payments should keep balance at 0
            if self.status == 'paid' and not payments:
                self.balance = Decimal('0.00')
            # If no payments and it's draft, balance = total
            elif not payments and (self.status == 'draft' or self.status is None):
                self.balance = self.total
            else:
                self.balance = self.total - total_paid
                if self.balance < 0:
                    self.balance = Decimal('0.00')
            
            if self.balance <= 0 and self.total > 0 and self.status != 'draft':
                self.status = 'paid'
                
        return self.total

    def __repr__(self):
        return f'<Bill {self.bill_number}>'

    @property
    def tax_breakdown(self):
        """
        Calculate breakdown of taxes.
        """
        breakdown = {}
        for line in self.lines:
            subtotal = Decimal(str(line.quantity)) * Decimal(str(line.unit_cost))
            if line.taxes:
                for tax in line.taxes:
                    tax_amount = (subtotal * Decimal(str(tax.rate))).quantize(Decimal('0.01'))
                    if tax.id in breakdown:
                        breakdown[tax.id]["amount"] += tax_amount
                    else:
                        breakdown[tax.id] = {
                            "id": tax.id,
                            "name": tax.name,
                            "amount": tax_amount,
                            "asset_account_id": tax.asset_account_id,
                            "liability_account_id": tax.liability_account_id
                        }
        
        # Sort by name for consistency
        sorted_ids = sorted(breakdown.keys(), key=lambda tid: breakdown[tid]["name"])
        return [breakdown[tid] for tid in sorted_ids]

class BillLine(db.Model, BaseModel):
    __tablename__ = 'bill_lines'
    __table_args__ = (
        db.CheckConstraint('quantity > 0', name='check_bill_line_quantity_positive'),
        db.CheckConstraint('unit_cost >= 0', name='check_bill_line_unit_cost_positive'),
    )
    
    bill_id = db.Column(db.Integer, db.ForeignKey('bills.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=True)
    description = db.Column(db.String(255))
    quantity = db.Column(db.Numeric(precision=20, scale=2), default=1.0)
    unit_cost = db.Column(db.Numeric(precision=20, scale=2), default=0.0)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False) # The expense/asset account
    line_total = db.Column(db.Numeric(precision=20, scale=2), default=0.0)
    
    # Relationships
    item = db.relationship('Item', backref='bill_lines')
    account = db.relationship('Account', backref='bill_lines')
    taxes = db.relationship('Tax', secondary='bill_line_taxes')

    def calculate_line_total(self):
        self.line_total = (Decimal(str(self.quantity)) * Decimal(str(self.unit_cost))).quantize(Decimal('0.01'))
        return self.line_total

    def calculate_tax_amount(self):
        subtotal = Decimal(str(self.quantity)) * Decimal(str(self.unit_cost))
        total_tax = Decimal('0.00')
        if self.taxes:
            for tax in self.taxes:
                total_tax += (subtotal * Decimal(str(tax.rate))).quantize(Decimal('0.01'))
        return total_tax

    def __repr__(self):
        return f'<BillLine {self.id} - {self.description}>'

# 3.4.1 Auto-update bill totals on line changes
@event.listens_for(db.session, 'before_flush')
def before_flush(session, flush_context, instances):
    bills_to_update = set()
    vendors_to_update = set()

    for obj in session.new | session.dirty:
        if isinstance(obj, BillLine):
            # Pre-fill from Item if item_id is set and fields are not provided
            if obj.item_id:
                with session.no_autoflush:
                    from .item import Item
                    item = session.get(Item, obj.item_id)
                    if item:
                        if not obj.description:
                            obj.description = item.description
                        if not obj.unit_cost or obj.unit_cost == 0:
                            obj.unit_cost = item.price
                        if not obj.account_id and item.expense_account_id:
                            obj.account_id = item.expense_account_id

            obj.calculate_line_total()
            if obj.bill:
                bills_to_update.add(obj.bill)
            elif obj.bill_id:
                with session.no_autoflush:
                    bill = session.get(Bill, obj.bill_id)
                    if bill:
                        bills_to_update.add(bill)
        elif isinstance(obj, Bill):
            bills_to_update.add(obj)
        else:
            # Handle VendorPayment
            from .payment import VendorPayment
            if isinstance(obj, VendorPayment):
                if obj.bill:
                    bills_to_update.add(obj.bill)
                elif obj.bill_id:
                    with session.no_autoflush:
                        bill = session.get(Bill, obj.bill_id)
                        if bill:
                            bills_to_update.add(bill)
                if obj.vendor:
                    vendors_to_update.add(obj.vendor)

    for obj in session.deleted:
        if isinstance(obj, BillLine):
            if obj.bill:
                bills_to_update.add(obj.bill)
            elif obj.bill_id:
                with session.no_autoflush:
                    bill = session.get(Bill, obj.bill_id)
                    if bill:
                        bills_to_update.add(bill)
        elif isinstance(obj, Bill):
            if obj.vendor:
                vendors_to_update.add(obj.vendor)
        else:
            # Handle VendorPayment
            from .payment import VendorPayment
            if isinstance(obj, VendorPayment):
                if obj.bill:
                    bills_to_update.add(obj.bill)
                elif obj.bill_id:
                    with session.no_autoflush:
                        bill = session.get(Bill, obj.bill_id)
                        if bill:
                            bills_to_update.add(bill)
                if obj.vendor:
                    vendors_to_update.add(obj.vendor)

    for bill in bills_to_update:
        if bill not in session.deleted:
            bill.calculate_totals()
            vendor = bill.vendor
            if not vendor and bill.vendor_id:
                with session.no_autoflush:
                    from .vendor import Vendor
                    vendor = session.get(Vendor, bill.vendor_id)
            if vendor:
                vendors_to_update.add(vendor)

    for vendor in vendors_to_update:
        if vendor not in session.deleted:
            with session.no_autoflush:
                # Start with bills already in the collection
                bills = list(vendor.bills)
                
                # Add new bills for this vendor that are in the session but not yet in the collection
                for obj in session.new:
                    if isinstance(obj, Bill) and (obj.vendor == vendor or obj.vendor_id == vendor.id):
                        if obj not in bills:
                            bills.append(obj)
                
                # Calculate total balance excluding deleted ones
                total_balance = sum(b.balance for b in bills if b.status != 'cancelled' and b not in session.deleted)
                vendor.balance = total_balance
