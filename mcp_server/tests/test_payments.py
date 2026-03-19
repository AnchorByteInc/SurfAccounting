from datetime import date
from mcp_server.tools.payments import (
    create_customer_payment,
    create_vendor_payment,
    mark_invoice_as_paid,
    mark_bill_as_paid
)
from mcp_server.schemas import (
    PaymentCreateSchema,
    VendorPaymentCreateSchema,
    PaymentDetailsSchema,
    InvoiceCreateSchema,
    InvoiceLineSchema,
    BillCreateSchema,
    BillLineSchema
)
from mcp_server.tools.invoices import create_invoice, approve_invoice, get_invoice
from mcp_server.tools.bills import create_bill, approve_bill, get_bill
from backend.models import Customer, Vendor, Account
from backend.extensions import db

def test_create_customer_payment():
    customer = Customer(name="Pay Customer")
    account = Account(name="Sales", code="4000", type="Revenue")
    ar_account = Account(name="A/R", code="1200", type="Asset", subtype="Accounts Receivable")
    bank_account = Account(name="Bank", code="1000", type="Asset")
    db.session.add_all([customer, account, ar_account, bank_account])
    db.session.commit()
    
    schema = InvoiceCreateSchema(
        customer_id=customer.id,
        issue_date=date.today(),
        due_date=date.today(),
        invoice_number="INV-P1",
        lines=[InvoiceLineSchema(description="X", quantity=1, unit_price=100, account_id=account.id)]
    )
    create_invoice(schema)
    approve_invoice(1)
    
    payment_schema = PaymentCreateSchema(
        customer_id=customer.id,
        amount=50.0,
        date=date.today(),
        invoice_id=1,
        account_id=bank_account.id
    )
    result = create_customer_payment(payment_schema)
    assert "Successfully created customer payment" in result
    
    inv_details = get_invoice(1)
    assert "Balance: 50.00" in inv_details

def test_mark_invoice_as_paid():
    customer = Customer(name="Paid Customer")
    account = Account(name="Sales", code="4000", type="Revenue")
    ar_account = Account(name="A/R", code="1200", type="Asset", subtype="Accounts Receivable")
    bank_account = Account(name="Bank", code="1000", type="Asset")
    db.session.add_all([customer, account, ar_account, bank_account])
    db.session.commit()
    
    schema = InvoiceCreateSchema(
        customer_id=customer.id,
        issue_date=date.today(),
        due_date=date.today(),
        invoice_number="INV-P2",
        lines=[InvoiceLineSchema(description="X", quantity=1, unit_price=200, account_id=account.id)]
    )
    create_invoice(schema)
    approve_invoice(1)
    
    details = PaymentDetailsSchema(date=date.today(), account_id=bank_account.id)
    result = mark_invoice_as_paid(1, details)
    assert "Successfully marked invoice INV-P2 as paid" in result
    
    inv_details = get_invoice(1)
    assert "Balance: 0.00" in inv_details
    assert "Status: paid" in inv_details

def test_create_vendor_payment():
    vendor = Vendor(name="Pay Vendor")
    account = Account(name="Expense", code="5000", type="Expense")
    ap_account = Account(name="A/P", code="2000", type="Liability", subtype="Accounts Payable")
    bank_account = Account(name="Bank", code="1000", type="Asset")
    db.session.add_all([vendor, account, ap_account, bank_account])
    db.session.commit()
    
    schema = BillCreateSchema(
        vendor_id=vendor.id,
        bill_number="BILL-P1",
        issue_date=date.today(),
        due_date=date.today(),
        lines=[BillLineSchema(description="X", quantity=1, unit_price=300, account_id=account.id)]
    )
    create_bill(schema)
    approve_bill(1)
    
    payment_schema = VendorPaymentCreateSchema(
        vendor_id=vendor.id,
        amount=100.0,
        date=date.today(),
        bill_id=1,
        account_id=bank_account.id
    )
    result = create_vendor_payment(payment_schema)
    assert "Successfully created vendor payment" in result
    
    bill_details = get_bill(1)
    assert "Balance: 200.00" in bill_details

def test_mark_bill_as_paid():
    vendor = Vendor(name="Paid Vendor")
    account = Account(name="Expense", code="5000", type="Expense")
    ap_account = Account(name="A/P", code="2000", type="Liability", subtype="Accounts Payable")
    bank_account = Account(name="Bank", code="1000", type="Asset")
    db.session.add_all([vendor, account, ap_account, bank_account])
    db.session.commit()
    
    schema = BillCreateSchema(
        vendor_id=vendor.id,
        bill_number="BILL-P2",
        issue_date=date.today(),
        due_date=date.today(),
        lines=[BillLineSchema(description="X", quantity=1, unit_price=400, account_id=account.id)]
    )
    create_bill(schema)
    approve_bill(1)
    
    details = PaymentDetailsSchema(date=date.today(), account_id=bank_account.id)
    result = mark_bill_as_paid(1, details)
    assert "Successfully marked bill BILL-P2 as paid" in result
    
    bill_details = get_bill(1)
    assert "Balance: 0.00" in bill_details
    assert "Status: paid" in bill_details
