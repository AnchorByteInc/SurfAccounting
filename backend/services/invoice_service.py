from ..extensions import db
from ..models.invoice import Invoice
from ..models.journal import JournalEntry, JournalEntryLine
from ..models.account import Account
from ..models.customer import Customer
from ..utils.validation import validate_date_is_open, validate_positive_amount, validate_date_order
from ..utils.money import to_decimal, zero

def sync_invoice_journal(invoice, delete=False):
    """
    Creates or updates the GL journal entry for an invoice.
    3.2.4 Generate journal entry for invoice (Debit A/R, Credit Revenue)
    """
    if not invoice:
        return
    
    with db.session.no_autoflush:
        # If invoice is deleted or draft or cancelled or has no lines, delete existing journal entry
        # Journal entries are only for approved, sent, paid, or overdue invoices.
        valid_statuses = ['approved', 'sent', 'paid', 'overdue']
        if delete or invoice.status not in valid_statuses or not invoice.lines:
            # If a journal entry exists, delete it
            if invoice.id:
                existing_journal = JournalEntry.query.filter_by(source_module="INV", source_id=invoice.id).first()
                if existing_journal:
                    db.session.delete(existing_journal)
            return

        # Find existing journal entry or create new one
        journal_entry = None
        if invoice.id:
            # Check session first to avoid double creation during the same flush cycle
            for obj in db.session.new | db.session.dirty:
                if isinstance(obj, JournalEntry) and obj.source_module == "INV" and obj.source_id == invoice.id:
                    journal_entry = obj
                    break
            
            if not journal_entry:
                journal_entry = JournalEntry.query.filter_by(source_module="INV", source_id=invoice.id).first()
        
        if not journal_entry:
            journal_entry = JournalEntry(
                source_module="INV",
                source_id=invoice.id,
                transaction_type="Invoice"
            )
            db.session.add(journal_entry)

        # Update journal entry fields
        journal_entry.date = invoice.issue_date
        journal_entry.memo = f"Invoice {invoice.invoice_number}"
        journal_entry.reference = f"INV-{invoice.invoice_number}"
        journal_entry.customer_id = invoice.customer_id
        if invoice.id:
            journal_entry.source_id = invoice.id
        
        # Clear existing lines and rebuild them
        # (Cascade delete-orphan handles the actual deletion)
        journal_entry.lines = []
        
        # Get Accounts Receivable account
        ar_account = Account.query.filter_by(subtype='Accounts Receivable').first()
        if not ar_account:
            ar_account = Account.query.filter_by(code='1200').first()
        
        if not ar_account:
            raise ValueError("Accounts Receivable account not found")

        # Debit A/R for the full invoice total
        ar_line = JournalEntryLine(
            account_id=ar_account.id,
            debit=to_decimal(invoice.total or zero()),
            credit=zero(),
            description=f"Accounts Receivable - Invoice {invoice.invoice_number}"
        )
        journal_entry.lines.append(ar_line)
        
        # Credit Revenue for each line
        for line in invoice.lines:
            revenue_line = JournalEntryLine(
                account_id=line.account_id,
                debit=zero(),
                credit=to_decimal(line.line_total or zero()),
                description=line.description
            )
            journal_entry.lines.append(revenue_line)
            
        # Handle Tax if any
        tax_breakdown = invoice.tax_breakdown
        for tax_item in tax_breakdown:
            amount = to_decimal(tax_item['amount'])
            if amount <= 0:
                continue
            
            tax_account_id = tax_item.get('liability_account_id')
            if not tax_account_id:
                # fallback to default
                tax_account = Account.query.filter_by(name='Sales Tax Payable').first()
                if not tax_account:
                     tax_account = Account.query.filter_by(code='2200').first()
                
                if not tax_account:
                    raise ValueError("Sales Tax Payable account not found")
                tax_account_id = tax_account.id
                
            tax_line = JournalEntryLine(
                account_id=tax_account_id,
                debit=zero(),
                credit=amount,
                description=f"Tax ({tax_item['name']}) - Invoice {invoice.invoice_number}"
            )
            journal_entry.lines.append(tax_line)

def post_invoice(invoice_id):
    """
    Finalizes an invoice:
    3.2.4 Generate journal entry for invoice (Debit A/R, Credit Revenue)
    3.2.5 Update customer A/R balance
    Also validates that the date is not in a closed period (10.1.6).
    """
    invoice = db.session.get(Invoice, invoice_id)
    if not invoice:
        raise ValueError(f"Invoice with id {invoice_id} not found")
    
    # 10.1.1 Validation edge cases
    validate_date_order(invoice.issue_date, invoice.due_date)
    
    if not invoice.lines:
        raise ValueError("Cannot post an invoice with no lines.")
        
    for line in invoice.lines:
        validate_positive_amount(line.quantity, f"Line '{line.description}' quantity")
        validate_positive_amount(line.unit_price, f"Line '{line.description}' unit price")

    validate_date_is_open(invoice.issue_date)
    
    # Ensure totals are up to date before posting
    invoice.calculate_totals()
    
    if invoice.total <= 0:
        raise ValueError("Invoice total must be greater than zero.")
    
    if invoice.status != 'draft':
        raise ValueError(f"Invoice {invoice.invoice_number} is already posted or cancelled")

    # Update invoice status to sent
    invoice.status = 'sent'
    
    # Generate/Sync journal entry
    sync_invoice_journal(invoice)
    
    # 3.2.5 Update customer A/R balance
    update_customer_balance(invoice.customer_id)
    
    db.session.flush()
    return invoice

def update_customer_balance(customer_id):
    """
    3.2.5 Update customer A/R balance
    Recalculates the total balance for a customer based on their invoices.
    """
    customer = db.session.get(Customer, customer_id)
    if not customer:
        raise ValueError(f"Customer with id {customer_id} not found")
    
    # Sum of all invoice balances
    total_balance = sum(invoice.balance for invoice in customer.invoices if invoice.status != 'cancelled')
    customer.balance = total_balance
    
    db.session.add(customer)
    return customer
