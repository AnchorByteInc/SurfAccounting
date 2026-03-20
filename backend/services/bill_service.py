from ..extensions import db
from ..models.bill import Bill
from ..models.journal import JournalEntry, JournalEntryLine
from ..models.account import Account
from ..models.vendor import Vendor
from ..utils.validation import validate_date_is_open, validate_positive_amount, validate_date_order
from decimal import Decimal
from ..utils.money import to_decimal, zero

def post_bill(bill_id):
    """
    Finalizes a bill:
    3.4.2 Generate journal entry (Debit Expense, Credit A/P)
    3.4.3 Update vendor A/P balance
    Also validates that the date is not in a closed period (10.1.6).
    """
    bill = db.session.get(Bill, bill_id)
    if not bill:
        raise ValueError(f"Bill with id {bill_id} not found")
    
    # 10.1.1 Validation edge cases
    validate_date_order(bill.issue_date, bill.due_date)
    
    if not bill.lines:
        raise ValueError("Cannot post a bill with no lines.")
        
    for line in bill.lines:
        validate_positive_amount(line.quantity, f"Line '{line.description}' quantity")
        validate_positive_amount(line.unit_cost, f"Line '{line.description}' unit cost")

    validate_date_is_open(bill.issue_date)
    
    if bill.status != 'draft':
        raise ValueError(f"Bill {bill.bill_number} is already approved or cancelled")

    # 3.4.1 Calculate bill totals
    bill.calculate_totals()

    # Update bill status
    bill.status = 'approved'
    
    # Sync GL
    sync_bill_gl(bill.id)
    
    # 3.4.3 Update vendor A/P balance
    update_vendor_balance(bill.vendor_id)
    
    db.session.flush()
    return bill

def sync_bill_gl(bill_id):
    """
    Creates or updates the GL transaction for a bill.
    Used when a bill is approved or edited after approval.
    """
    bill = db.session.get(Bill, bill_id)
    if not bill:
        return

    with db.session.no_autoflush:
        # Only sync for approved/paid/overdue status
        if bill.status not in ['approved', 'paid', 'overdue'] or not bill.lines:
            existing_je = JournalEntry.query.filter_by(source_module="BILL", source_id=bill.id).first()
            if existing_je:
                db.session.delete(existing_je)
            return

        # Find or create JournalEntry
        journal_entry = None
        if bill.id:
            # Check session first to avoid double creation during the same flush cycle
            for obj in db.session.new | db.session.dirty:
                if isinstance(obj, JournalEntry) and obj.source_module == "BILL" and obj.source_id == bill.id:
                    journal_entry = obj
                    break
            
            if not journal_entry:
                journal_entry = JournalEntry.query.filter_by(source_module="BILL", source_id=bill.id).first()
        
        if not journal_entry:
            journal_entry = JournalEntry(
                source_module="BILL",
                source_id=bill.id,
                transaction_type="Bill"
            )
            db.session.add(journal_entry)

        # Ensure totals are up to date
        bill.calculate_totals()

        # Update header
        journal_entry.date = bill.issue_date
        journal_entry.memo = f"Bill {bill.bill_number}"
        journal_entry.reference = f"BILL-{bill.bill_number}"
        journal_entry.vendor_id = bill.vendor_id

        # Clear existing lines to rebuild them
        journal_entry.lines = []

        # Get Accounts Payable account
        ap_account = Account.query.filter_by(subtype='Accounts Payable').first()
        if not ap_account:
            ap_account = Account.query.filter_by(code='2000').first()
        
        if not ap_account:
            raise ValueError("Accounts Payable account not found")

        # Credit A/P for the full bill total
        ap_line = JournalEntryLine(
            account_id=ap_account.id,
            debit=zero(),
            credit=to_decimal(bill.total),
            description=f"Accounts Payable - Bill {bill.bill_number}"
        )
        journal_entry.lines.append(ap_line)
        
        # Debit Expense (or asset) for each line
        for line in bill.lines:
            expense_line = JournalEntryLine(
                account_id=line.account_id,
                debit=to_decimal(line.line_total),
                credit=zero(),
                description=line.description
            )
            journal_entry.lines.append(expense_line)
            
            # Handle taxes that revert to line account (no asset_account_id)
            if line.taxes:
                line_subtotal = Decimal(str(line.quantity)) * Decimal(str(line.unit_cost))
                for tax in line.taxes:
                    if not tax.asset_account_id:
                        tax_amount = (line_subtotal * Decimal(str(tax.rate))).quantize(Decimal('0.01'))
                        if tax_amount > 0:
                            tax_line = JournalEntryLine(
                                account_id=line.account_id,
                                debit=tax_amount,
                                credit=zero(),
                                description=f"Tax ({tax.name}) - {line.description}"
                            )
                            journal_entry.lines.append(tax_line)

        # Handle Tax breakdown for taxes with asset_account_id
        tax_breakdown = bill.tax_breakdown
        for tax_item in tax_breakdown:
            amount = to_decimal(tax_item['amount'])
            if amount <= 0:
                continue
            
            tax_account_id = tax_item.get('asset_account_id')
            if tax_account_id:
                tax_line = JournalEntryLine(
                    account_id=tax_account_id,
                    debit=amount,
                    credit=zero(),
                    description=f"Tax ({tax_item['name']}) - Bill {bill.bill_number}"
                )
                journal_entry.lines.append(tax_line)

def update_vendor_balance(vendor_id):
    """
    3.4.3 Update vendor A/P balance
    Recalculates the total balance for a vendor based on their bills.
    """
    vendor = db.session.get(Vendor, vendor_id)
    if not vendor:
        raise ValueError(f"Vendor with id {vendor_id} not found")
    
    # Sum of all bill balances
    # We only include bills that are not cancelled.
    total_balance = sum(bill.balance for bill in vendor.bills if bill.status != 'cancelled')
    vendor.balance = total_balance
    
    db.session.add(vendor)
    return vendor

def void_bill(bill_id):
    """
    Voids a bill:
    1. Sets status to 'cancelled'
    2. Reverses accounting entries (sync_bill_gl will delete the journal entry)
    3. Updates vendor A/P balance
    """
    bill = db.session.get(Bill, bill_id)
    if not bill:
        raise ValueError(f"Bill with id {bill_id} not found")
    
    if bill.status == 'cancelled':
        return bill
        
    if bill.status == 'paid':
         raise ValueError(f"Cannot void bill {bill.bill_number} because it is already paid. Please void payments first.")

    bill.status = 'cancelled'
    bill.calculate_totals() # This will set balance to 0 as per Bill model
    
    # Sync GL (this will delete the JournalEntry because status is 'cancelled')
    sync_bill_gl(bill.id)
    
    # Update vendor balance
    update_vendor_balance(bill.vendor_id)
    
    return bill

def get_unpaid_bills(vendor_id=None):
    """
    Returns a list of bills that have a balance > 0 and are not draft or cancelled.
    """
    query = Bill.query.filter(Bill.balance > 0, Bill.status.in_(['approved', 'overdue']))
    if vendor_id:
        query = query.filter(Bill.vendor_id == vendor_id)
    return query.all()
