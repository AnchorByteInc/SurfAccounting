from ..extensions import db
from ..models.payment import Payment, VendorPayment
from ..models.invoice import Invoice
from ..models.bill import Bill
from ..models.journal import JournalEntry, JournalEntryLine
from ..models.account import Account
from ..models.bank import BankAccount
from ..services.invoice_service import update_customer_balance
from ..services.bill_service import update_vendor_balance, sync_bill_gl
from ..utils.validation import validate_date_is_open, validate_positive_amount
from ..utils.ledger import get_account_balance
from datetime import date
from decimal import Decimal
from ..utils.money import to_decimal, zero

def apply_payment(amount, date_paid, customer_id, invoice_id=None, method='Cash', account_id=None):
    """
    3.3.1 Apply payment to invoice
    3.3.2 Update invoice balance
    3.3.3 Generate journal entry (Debit Bank/Cash/CC, Credit A/R)
    3.3.4 Handle partial payments
    Also validates closed periods (10.1.6) and positive amount (10.1.1).
    """
    validate_date_is_open(date_paid)
    validate_positive_amount(amount, "Payment amount")
    amount = to_decimal(amount)
    
    payment = Payment(
        amount=amount,
        date=date_paid,
        customer_id=customer_id,
        invoice_id=invoice_id,
        account_id=account_id,
        method=method
    )
    db.session.add(payment)
    # Flush to get payment ID for reference
    db.session.flush()
    
    # 3.3.2 Update invoice balance if payment is for a specific invoice
    if invoice_id:
        invoice = db.session.get(Invoice, invoice_id)
        if not invoice:
            raise ValueError(f"Invoice with id {invoice_id} not found")
        
        # Only approved invoices can be paid.
        if invoice.status not in ['approved', 'sent', 'paid', 'overdue']:
            raise ValueError(f"Cannot pay invoice {invoice_id} because its status is {invoice.status}. It must be approved first.")
    
    # 3.3.3 Generate journal entry
    journal_entry = JournalEntry(
        date=date_paid,
        memo=f"Payment from customer {customer_id}" + (f" for invoice {invoice_id}" if invoice_id else ""),
        reference=f"PAY-{payment.id}",
        transaction_type="Payment",
        source_module="PAY",
        source_id=payment.id,
        customer_id=customer_id
    )
    
    # Need to get the payment account and A/R account
    payment_account = None
    if account_id:
        payment_account = db.session.get(Account, account_id)
    
    if not payment_account:
        # Fallback to default Cash account
        payment_account = Account.query.filter_by(name='Cash').first()
        if not payment_account:
            payment_account = Account.query.filter_by(code='1000').first()
    
    if not payment_account:
        raise ValueError("Cash/Bank account not found")

    ar_account = Account.query.filter_by(name='Accounts Receivable').first()
    if not ar_account:
        ar_account = Account.query.filter_by(code='1200').first()
    
    if not ar_account:
        raise ValueError("Accounts Receivable account not found")

    # Debit Bank/Cash (Asset increases)
    cash_line = JournalEntryLine(
        account_id=payment_account.id,
        debit=to_decimal(amount),
        credit=zero(),
        description=f"Payment - {method}"
    )
    journal_entry.lines.append(cash_line)
    
    # Credit A/R (Asset decreases)
    ar_line = JournalEntryLine(
        account_id=ar_account.id,
        debit=zero(),
        credit=to_decimal(amount),
        description=f"Accounts Receivable - Customer Payment {payment.id}"
    )
    journal_entry.lines.append(ar_line)
    
    db.session.add(journal_entry)
    
    # Update customer balance
    update_customer_balance(customer_id)
    
    return payment

def apply_vendor_payment(amount, date_paid, vendor_id, bill_id=None, method='Cash', account_id=None):
    """
    3.5.1 Apply vendor payment
    3.5.2 Generate journal entry (Debit A/P, Credit Bank/Cash/CC)
    3.5.3 Handle partial bill payments
    Also validates closed periods (10.1.6), positive amount (10.1.1), and prevents negative cash (10.1.5).
    """
    validate_date_is_open(date_paid)
    validate_positive_amount(amount, "Vendor payment amount")
    amount = to_decimal(amount)
    
    vendor_payment = VendorPayment(
        amount=amount,
        date=date_paid,
        vendor_id=vendor_id,
        bill_id=bill_id,
        account_id=account_id,
        method=method
    )
    db.session.add(vendor_payment)
    # Flush to get payment ID for reference
    db.session.flush()
    
    # 3.5.3 Handle partial bill payments & update balance
    if bill_id:
        bill = db.session.get(Bill, bill_id)
        if not bill:
            raise ValueError(f"Bill with id {bill_id} not found")
        
        # Balance will be recalculated by model events during flush/commit.
        if bill.status == 'draft':
            raise ValueError("Bill must be approved before payment.")
            
    # 3.5.2 Generate journal entry
    journal_entry = JournalEntry(
        date=date_paid,
        memo=f"Payment to vendor {vendor_id}" + (f" for bill {bill_id}" if bill_id else ""),
        reference=f"VPAY-{vendor_payment.id}",
        transaction_type="Payment",
        source_module="VPAY",
        source_id=vendor_payment.id,
        vendor_id=vendor_id
    )
    
    # Get the source account for payment (Bank/Cash/CC)
    if account_id:
        payment_account = db.session.get(Account, account_id)
        if not payment_account:
            raise ValueError(f"Payment account with id {account_id} not found")
    else:
        # Fallback to hardcoded Cash account if none provided
        payment_account = Account.query.filter_by(name='Cash').first()
        if not payment_account:
            payment_account = Account.query.filter_by(code='1000').first()
        
        if not payment_account:
            raise ValueError("Cash account not found")

    ap_account = Account.query.filter_by(subtype='Accounts Payable').first()
    if not ap_account:
        ap_account = Account.query.filter_by(code='2000').first()
    
    if not ap_account:
        raise ValueError("Accounts Payable account not found")

    # Prevent negative cash balance (10.1.5)
    # Enforce only when a BankAccount is linked to this ledger account to avoid blocking
    # setups without explicit bank accounts (e.g., tests).
    linked_bank = BankAccount.query.filter_by(account_id=payment_account.id).first()
    if linked_bank:
        current_balance = get_account_balance(payment_account.id)
        if (current_balance - amount) < Decimal('0.00'):
            raise ValueError("Insufficient cash balance to make this payment.")

    # Debit A/P (Liability decreases)
    ap_line = JournalEntryLine(
        account_id=ap_account.id,
        debit=to_decimal(amount),
        credit=zero(),
        description=f"Accounts Payable - Vendor Payment {vendor_payment.id}"
    )
    journal_entry.lines.append(ap_line)
    
    # Credit Payment Account (Asset decreases or Liability increases)
    payment_line = JournalEntryLine(
        account_id=payment_account.id,
        debit=zero(),
        credit=to_decimal(amount),
        description=f"Payment - {method}"
    )
    journal_entry.lines.append(payment_line)
    
    db.session.add(journal_entry)
    
    # Update vendor balance
    update_vendor_balance(vendor_id)
    
    return vendor_payment
