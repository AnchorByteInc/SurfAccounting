from datetime import date
from mcp_server.tools.bills import (
    create_bill,
    get_bill,
    approve_bill,
    void_bill,
    get_unpaid_bills
)
from mcp_server.schemas import BillCreateSchema, BillLineSchema
from backend.models import Vendor, Account
from backend.extensions import db

def test_create_bill():
    vendor = Vendor(name="Bill Vendor")
    account = Account(name="Expense", code="5000", type="Expense")
    db.session.add_all([vendor, account])
    db.session.commit()
    
    schema = BillCreateSchema(
        vendor_id=vendor.id,
        bill_number="BILL-001",
        issue_date=date.today(),
        due_date=date.today(),
        lines=[
            BillLineSchema(
                description="Purchase 1",
                quantity=1.0,
                unit_price=150.0,
                account_id=account.id
            )
        ]
    )
    result = create_bill(schema)
    assert "Successfully created draft bill 'BILL-001'" in result
    assert "Total: 150" in result

def test_approve_bill():
    vendor = Vendor(name="Approve Vendor")
    account = Account(name="Expense", code="5000", type="Expense")
    ap_account = Account(name="A/P", code="2000", type="Liability", subtype="Accounts Payable")
    db.session.add_all([vendor, account, ap_account])
    db.session.commit()
    
    schema = BillCreateSchema(
        vendor_id=vendor.id,
        bill_number="BILL-002",
        issue_date=date.today(),
        due_date=date.today(),
        lines=[
            BillLineSchema(
                description="Purchase 2",
                quantity=1.0,
                unit_price=200.0,
                account_id=account.id
            )
        ]
    )
    create_bill(schema)
    
    result = approve_bill(1)
    assert "Successfully approved and posted" in result
    
    bill_details = get_bill(1)
    assert "Status: approved" in bill_details

def test_void_bill():
    vendor = Vendor(name="Void Vendor")
    account = Account(name="Expense", code="5000", type="Expense")
    ap_account = Account(name="A/P", code="2000", type="Liability", subtype="Accounts Payable")
    db.session.add_all([vendor, account, ap_account])
    db.session.commit()
    
    schema = BillCreateSchema(
        vendor_id=vendor.id,
        bill_number="BILL-003",
        issue_date=date.today(),
        due_date=date.today(),
        lines=[BillLineSchema(description="X", quantity=1, unit_price=10, account_id=account.id)]
    )
    create_bill(schema)
    approve_bill(1)
    
    result = void_bill(1)
    assert "Successfully voided" in result
    
    bill_details = get_bill(1)
    assert "Status: cancelled" in bill_details

def test_get_unpaid_bills():
    vendor = Vendor(name="Unpaid Vendor")
    account = Account(name="Expense", code="5000", type="Expense")
    ap_account = Account(name="A/P", code="2000", type="Liability", subtype="Accounts Payable")
    db.session.add_all([vendor, account, ap_account])
    db.session.commit()
    
    schema = BillCreateSchema(
        vendor_id=vendor.id,
        bill_number="BILL-004",
        issue_date=date.today(),
        due_date=date.today(),
        lines=[BillLineSchema(description="X", quantity=1, unit_price=75, account_id=account.id)]
    )
    create_bill(schema)
    approve_bill(1)
    
    result = get_unpaid_bills(vendor.id)
    assert "BILL-004" in result
    assert "Balance: 75" in result
