from sqlalchemy import event
from ..extensions import db
from .base import BaseModel
from decimal import Decimal

class Invoice(db.Model, BaseModel):
    __tablename__ = 'invoices'
    __table_args__ = (
        db.CheckConstraint('total >= 0', name='check_invoice_total_positive'),
        db.CheckConstraint('balance >= 0', name='check_invoice_balance_positive'),
        db.CheckConstraint('due_date >= issue_date', name='check_invoice_due_date_after_issue'),
    )
    
    customer_id = db.Column(db.Integer, db.ForeignKey('customers.id'), nullable=False, index=True)
    invoice_number = db.Column(db.String(50), unique=True, nullable=False)
    issue_date = db.Column(db.Date, nullable=False, index=True)
    due_date = db.Column(db.Date, nullable=False)
    status = db.Column(db.String(20), default='draft', index=True) # draft, approved, sent, paid, overdue, cancelled
    subtotal = db.Column(db.Numeric(precision=20, scale=2), default=0.0)
    tax = db.Column(db.Numeric(precision=20, scale=2), default=0.0)
    total = db.Column(db.Numeric(precision=20, scale=2), default=0.0)
    balance = db.Column(db.Numeric(precision=20, scale=2), default=0.0)
    
    # 2.2.9 Relationships and cascade rules
    customer = db.relationship('Customer', backref='invoices')
    lines = db.relationship('InvoiceLine', backref='invoice', cascade='all, delete-orphan')

    def calculate_totals(self):
        """
        3.2.1 Implement invoice subtotal calculation
        3.2.2 Implement tax calculation
        """
        # Include lines already in the collection and new ones in the session
        lines_to_sum = list(self.lines)
        for obj in db.session.new:
            if isinstance(obj, InvoiceLine) and (obj.invoice == self or (self.id and obj.invoice_id == self.id)):
                if obj not in lines_to_sum:
                    lines_to_sum.append(obj)
                    
        # Exclude lines that are about to be deleted
        lines_to_sum = [line for line in lines_to_sum if line not in db.session.deleted]

        # If there are no lines but a positive total was already set (e.g., imported or preset invoice),
        # preserve existing totals and only recalculate balance from payments.
        preserve_existing_totals = (len(lines_to_sum) == 0 and self.total and Decimal(str(self.total)) > 0 and self.status != 'draft')

        if not preserve_existing_totals:
            self.subtotal = sum(line.calculate_line_total() for line in lines_to_sum)
            self.tax = sum(line.calculate_tax_amount() for line in lines_to_sum)
            self.total = self.subtotal + self.tax
        
        # When in draft, the balance should stay in sync with the total if no payments exist.
        # Once it's sent or paid, the balance is managed by payments (Phase 3.3)
        if self.status == 'cancelled':
            self.balance = Decimal('0.00')
        else:
            # Re-calculate balance based on payments
            with db.session.no_autoflush:
                from .payment import Payment
                # Query payments from DB (includes flushed but not committed)
                if self.id:
                    payments = db.session.query(Payment).filter_by(invoice_id=self.id).all()
                else:
                    payments = []
                
                # Also check session.new for payments not yet flushed
                for obj in db.session.new:
                    if isinstance(obj, Payment) and (obj.invoice == self or (self.id and obj.invoice_id == self.id)):
                        if obj not in payments:
                            payments.append(obj)
            
            total_paid = sum(p.amount for p in payments if p not in db.session.deleted)
            
            # Special case: an invoice marked as 'paid' with no recorded payments should keep balance at 0
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
        return f'<Invoice {self.invoice_number}>'

    @property
    def tax_breakdown(self):
        """
        Calculate breakdown of taxes.
        """
        breakdown = {}
        for line in self.lines:
            subtotal = Decimal(str(line.quantity)) * Decimal(str(line.unit_price))
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

class InvoiceLine(db.Model, BaseModel):
    __tablename__ = 'invoice_lines'
    __table_args__ = (
        db.CheckConstraint('quantity > 0', name='check_invoice_line_quantity_positive'),
        db.CheckConstraint('unit_price >= 0', name='check_invoice_line_unit_price_positive'),
    )
    
    invoice_id = db.Column(db.Integer, db.ForeignKey('invoices.id'), nullable=False)
    item_id = db.Column(db.Integer, db.ForeignKey('items.id'), nullable=True)
    description = db.Column(db.String(255))
    quantity = db.Column(db.Numeric(precision=20, scale=2), default=1.0)
    unit_price = db.Column(db.Numeric(precision=20, scale=2), default=0.0)
    account_id = db.Column(db.Integer, db.ForeignKey('accounts.id'), nullable=False)
    line_total = db.Column(db.Numeric(precision=20, scale=2), default=0.0)
    
    # Relationships
    item = db.relationship('Item', backref='invoice_lines')
    account = db.relationship('Account', backref='invoice_lines')
    taxes = db.relationship('Tax', secondary='invoice_line_taxes')
    
    def calculate_line_total(self):
        self.line_total = (Decimal(str(self.quantity)) * Decimal(str(self.unit_price))).quantize(Decimal('0.01'))
        return self.line_total

    def calculate_tax_amount(self):
        subtotal = Decimal(str(self.quantity)) * Decimal(str(self.unit_price))
        total_tax = Decimal('0.00')
        if self.taxes:
            for tax in self.taxes:
                total_tax += (subtotal * Decimal(str(tax.rate))).quantize(Decimal('0.01'))
        return total_tax

    def __repr__(self):
        return f'<InvoiceLine {self.id} - {self.description}>'

# 3.2.3 Auto-update invoice totals on line changes
@event.listens_for(db.session, 'before_flush')
def before_flush(session, flush_context, instances):
    invoices_to_update = set()
    customers_to_update = set()

    for obj in session.new | session.dirty:
        if isinstance(obj, InvoiceLine):
            # Pre-fill from Item if item_id is set and fields are not provided
            if obj.item_id:
                with session.no_autoflush:
                    from .item import Item
                    item = session.get(Item, obj.item_id)
                    if item:
                        if not obj.description:
                            obj.description = item.description
                        if not obj.unit_price or obj.unit_price == 0:
                            obj.unit_price = item.price
                        if not obj.account_id and item.income_account_id:
                            obj.account_id = item.income_account_id
                        if not obj.taxes and item.sales_taxes:
                            obj.taxes = list(item.sales_taxes)

            obj.calculate_line_total()
            if obj.invoice:
                invoices_to_update.add(obj.invoice)
            elif obj.invoice_id:
                with session.no_autoflush:
                    invoice = session.get(Invoice, obj.invoice_id)
                    if invoice:
                        invoices_to_update.add(invoice)
        elif isinstance(obj, Invoice):
            # Auto-generate invoice number if missing
            if not obj.invoice_number:
                with session.no_autoflush:
                    # Find the highest invoice number in DB
                    last_invoice = session.query(Invoice).filter(Invoice.invoice_number.like('INV-%')).order_by(Invoice.id.desc()).first()
                    last_num = 0
                    if last_invoice:
                        try:
                            last_num = int(last_invoice.invoice_number.split('-')[-1])
                        except (ValueError, IndexError):
                            pass
                    
                    # Also check session for new invoices that already have a number
                    for other in session.new:
                        if isinstance(other, Invoice) and other.invoice_number and other.invoice_number.startswith('INV-'):
                            try:
                                num = int(other.invoice_number.split('-')[-1])
                                if num > last_num:
                                    last_num = num
                            except (ValueError, IndexError):
                                pass
                    
                    obj.invoice_number = f"INV-{(last_num + 1):04d}"
            
            invoices_to_update.add(obj)
        else:
            # Handle Payment
            from .payment import Payment
            if isinstance(obj, Payment):
                if obj.invoice:
                    invoices_to_update.add(obj.invoice)
                elif obj.invoice_id:
                    with session.no_autoflush:
                        invoice = session.get(Invoice, obj.invoice_id)
                        if invoice:
                            invoices_to_update.add(invoice)
                if obj.customer:
                    customers_to_update.add(obj.customer)

    for obj in session.deleted:
        if isinstance(obj, InvoiceLine):
            if obj.invoice:
                invoices_to_update.add(obj.invoice)
            elif obj.invoice_id:
                with session.no_autoflush:
                    invoice = session.get(Invoice, obj.invoice_id)
                    if invoice:
                        invoices_to_update.add(invoice)
        elif isinstance(obj, Invoice):
            if obj.customer:
                customers_to_update.add(obj.customer)
        else:
            # Handle Payment
            from .payment import Payment
            if isinstance(obj, Payment):
                if obj.invoice:
                    invoices_to_update.add(obj.invoice)
                elif obj.invoice_id:
                    with session.no_autoflush:
                        invoice = session.get(Invoice, obj.invoice_id)
                        if invoice:
                            invoices_to_update.add(invoice)
                if obj.customer:
                    customers_to_update.add(obj.customer)

    for obj in session.deleted:
        if isinstance(obj, Invoice):
            with session.no_autoflush:
                from ..services.invoice_service import sync_invoice_journal
                sync_invoice_journal(obj, delete=True)

    for invoice in invoices_to_update:
        if invoice not in session.deleted:
            invoice.calculate_totals()
            customer = invoice.customer
            if not customer and invoice.customer_id:
                with session.no_autoflush:
                    from .customer import Customer
                    customer = session.get(Customer, invoice.customer_id)
            if customer:
                customers_to_update.add(customer)
            
            # Sync GL transactions if not draft and NOT a new invoice
            # New invoices are handled in after_insert to ensure they have an ID
            if invoice.id:
                with session.no_autoflush:
                    from ..services.invoice_service import sync_invoice_journal
                    sync_invoice_journal(invoice)

    for customer in customers_to_update:
        if customer not in session.deleted:
            with session.no_autoflush:
                # Start with invoices already in the collection
                invoices = list(customer.invoices)
                
                # Add new invoices for this customer that are in the session but not yet in the collection
                for obj in session.new:
                    if isinstance(obj, Invoice) and (obj.customer == customer or obj.customer_id == customer.id):
                        if obj not in invoices:
                            invoices.append(obj)
                
                # Calculate total balance excluding deleted ones
                total_balance = sum(inv.balance for inv in invoices if inv.status != 'cancelled' and inv not in session.deleted)
                customer.balance = total_balance

@event.listens_for(Invoice, 'after_insert')
def after_invoice_insert(mapper, connection, target):
    """Ensure GL transaction is created for new non-draft invoices"""
    from ..services.invoice_service import sync_invoice_journal
    sync_invoice_journal(target)
