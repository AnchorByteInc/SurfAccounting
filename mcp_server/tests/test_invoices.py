from datetime import date
from mcp_server.tools.invoices import (
    create_invoice,
    get_invoice,
    approve_invoice,
    void_invoice,
    get_unpaid_invoices
)
from mcp_server.schemas import InvoiceCreateSchema, InvoiceLineSchema
from backend.models import Customer, Account
from backend.extensions import db

def test_create_invoice():
    customer = Customer(name="Inv Customer")
    account = Account(name="Sales", code="4000", type="Revenue")
    db.session.add_all([customer, account])
    db.session.commit()
    
    schema = InvoiceCreateSchema(
        customer_id=customer.id,
        issue_date=date.today(),
        due_date=date.today(),
        invoice_number="INV-001",
        lines=[
            InvoiceLineSchema(
                description="Item 1",
                quantity=2.0,
                unit_price=50.0,
                account_id=account.id
            )
        ]
    )
    result = create_invoice(schema)
    assert "Successfully created draft invoice 'INV-001'" in result
    assert "Total: 100" in result

def test_approve_invoice():
    customer = Customer(name="Approve Customer")
    account = Account(name="Sales", code="4000", type="Revenue")
    ar_account = Account(name="A/R", code="1200", type="Asset", subtype="Accounts Receivable")
    db.session.add_all([customer, account, ar_account])
    db.session.commit()
    
    schema = InvoiceCreateSchema(
        customer_id=customer.id,
        issue_date=date.today(),
        due_date=date.today(),
        invoice_number="INV-002",
        lines=[
            InvoiceLineSchema(
                description="Item 1",
                quantity=1.0,
                unit_price=100.0,
                account_id=account.id
            )
        ]
    )
    create_invoice(schema)
    
    # Approve it
    result = approve_invoice(1)
    assert "Successfully approved and posted" in result
    
    # Check status
    inv_details = get_invoice(1)
    assert "Status: approved" in inv_details

def test_void_invoice():
    customer = Customer(name="Void Customer")
    account = Account(name="Sales", code="4000", type="Revenue")
    ar_account = Account(name="A/R", code="1200", type="Asset", subtype="Accounts Receivable")
    db.session.add_all([customer, account, ar_account])
    db.session.commit()
    
    schema = InvoiceCreateSchema(
        customer_id=customer.id,
        issue_date=date.today(),
        due_date=date.today(),
        invoice_number="INV-003",
        lines=[InvoiceLineSchema(description="X", quantity=1, unit_price=10, account_id=account.id)]
    )
    create_invoice(schema)
    approve_invoice(1)
    
    result = void_invoice(1)
    assert "Successfully voided" in result
    
    inv_details = get_invoice(1)
    assert "Status: cancelled" in inv_details

def test_get_unpaid_invoices():
    customer = Customer(name="Unpaid Customer")
    account = Account(name="Sales", code="4000", type="Revenue")
    ar_account = Account(name="A/R", code="1200", type="Asset", subtype="Accounts Receivable")
    db.session.add_all([customer, account, ar_account])
    db.session.commit()
    
    schema = InvoiceCreateSchema(
        customer_id=customer.id,
        issue_date=date.today(),
        due_date=date.today(),
        invoice_number="INV-004",
        lines=[InvoiceLineSchema(description="X", quantity=1, unit_price=50, account_id=account.id)]
    )
    create_invoice(schema)
    approve_invoice(1)
    
    result = get_unpaid_invoices(customer.id)
    assert "INV-004" in result
    assert "Balance: 50" in result
