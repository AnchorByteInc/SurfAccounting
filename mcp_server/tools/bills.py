from mcp_server.instance import mcp
from mcp_server.utils.db import get_db_session
from mcp_server.schemas import BillCreateSchema
from backend.extensions import db
from backend.models import Bill, Vendor, BillLine, Tax
from backend.services.bill_service import post_bill, update_vendor_balance, sync_bill_gl

# --- Section 5.1: Purchase Workflow: Bills ---

@mcp.tool()
def get_bills(vendor_id: int = None, status: str = None) -> str:
    """
    List bills, optionally filtered by vendor_id or status.
    """
    with get_db_session():
        query = Bill.query
        if vendor_id:
            query = query.filter(Bill.vendor_id == vendor_id)
        if status:
            query = query.filter(Bill.status == status)
        
        bills = query.all()
        if not bills:
            return "No bills found."
        
        result = "Bills:\n"
        for bill in bills:
            vendor_name = bill.vendor.name if bill.vendor else "Unknown"
            result += f"- ID: {bill.id}, Number: {bill.bill_number}, Vendor: {vendor_name}, Date: {bill.issue_date}, Total: {bill.total}, Status: {bill.status}\n"
        return result

@mcp.tool()
def get_bill(id: int) -> str:
    """
    Detailed view of a single bill, including its line items.
    """
    with get_db_session():
        bill = db.session.get(Bill, id)
        if not bill:
            return f"Bill with ID {id} not found."
        
        vendor_name = bill.vendor.name if bill.vendor else "Unknown"
        result = f"Bill #{bill.bill_number} (ID: {bill.id})\n"
        result += f"- Vendor: {vendor_name} (ID: {bill.vendor_id})\n"
        result += f"- Issue Date: {bill.issue_date}\n"
        result += f"- Due Date: {bill.due_date}\n"
        result += f"- Status: {bill.status}\n"
        result += f"- Subtotal: {bill.subtotal}\n"
        result += f"- Tax: {bill.tax}\n"
        result += f"- Total: {bill.total}\n"
        result += f"- Balance: {bill.balance}\n"
        result += "\nLine Items:\n"
        
        for line in bill.lines:
            result += f"  - {line.description or 'No description'}: {line.quantity} x {line.unit_cost} = {line.line_total} (Account: {line.account.name if line.account else 'N/A'})\n"
            
        return result

@mcp.tool()
def create_bill(bill_data: BillCreateSchema) -> str:
    """
    Create a new draft bill.
    """
    try:
        with get_db_session():
            vendor = db.session.get(Vendor, bill_data.vendor_id)
            if not vendor:
                return f"Error: Vendor with ID {bill_data.vendor_id} not found."

            new_bill = Bill(
                vendor_id=bill_data.vendor_id,
                bill_number=bill_data.bill_number,
                issue_date=bill_data.issue_date,
                due_date=bill_data.due_date,
                status='draft'
            )
            
            db.session.add(new_bill)
            db.session.flush()
            
            for line_data in bill_data.lines:
                line = BillLine(
                    item_id=line_data.item_id,
                    description=line_data.description,
                    quantity=line_data.quantity,
                    unit_cost=line_data.unit_price, # Bill uses unit_cost
                    account_id=line_data.account_id
                )
                if line_data.tax_ids:
                    line.taxes = db.session.query(Tax).filter(Tax.id.in_(line_data.tax_ids)).all()
                new_bill.lines.append(line)
            
            db.session.flush()
            return f"Successfully created draft bill '{new_bill.bill_number}' (ID: {new_bill.id}) with {len(new_bill.lines)} lines. Total: {new_bill.total}"
    except Exception as e:
        return f"Error creating bill: {str(e)}"

@mcp.tool()
def update_bill(id: int, vendor_id: int = None, bill_number: str = None, issue_date: str = None, due_date: str = None, status: str = None) -> str:
    """
    Update a draft bill. Only draft bills can be updated.
    """
    from datetime import datetime
    try:
        with get_db_session():
            bill = db.session.get(Bill, id)
            if not bill:
                return f"Bill with ID {id} not found."
            
            if bill.status != 'draft':
                return f"Cannot update bill {bill.bill_number} because it is in '{bill.status}' status (only 'draft' invoices can be updated)."
            
            updated_count = 0
            if vendor_id is not None:
                bill.vendor_id = vendor_id
                updated_count += 1
            if bill_number is not None:
                bill.bill_number = bill_number
                updated_count += 1
            if issue_date is not None:
                try:
                    bill.issue_date = datetime.strptime(issue_date, '%Y-%m-%d').date()
                    updated_count += 1
                except ValueError:
                    return "Error: Invalid issue_date format. Use YYYY-MM-DD."
            if due_date is not None:
                try:
                    bill.due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
                    updated_count += 1
                except ValueError:
                    return "Error: Invalid due_date format. Use YYYY-MM-DD."
            if status is not None:
                bill.status = status
                updated_count += 1
                
            if updated_count == 0:
                return "No valid fields provided for update."
                
            db.session.flush()
            return f"Successfully updated draft bill {bill.bill_number} (ID: {id})."
    except Exception as e:
        return f"Error updating bill: {str(e)}"

@mcp.tool()
def delete_bill(id: int) -> str:
    """
    Delete a draft bill. Only draft or unposted bills can be deleted.
    """
    try:
        with get_db_session():
            bill = db.session.get(Bill, id)
            if not bill:
                return f"Bill with ID {id} not found."
            
            if bill.status != 'draft':
                return f"Cannot delete bill {bill.bill_number} because it is in '{bill.status}' status (only 'draft' bills can be deleted)."
            
            db.session.delete(bill)
            return f"Successfully deleted draft bill {bill.bill_number} (ID: {id})."
    except Exception as e:
        return f"Error deleting bill: {str(e)}"

# --- Section 5.2: Purchase Workflow: Bill Processing ---

@mcp.tool()
def approve_bill(id: int) -> str:
    """
    Approve a draft bill, posting it to the ledger.
    """
    try:
        with get_db_session():
            bill = post_bill(id)
            return f"Successfully approved and posted bill '{bill.bill_number}' (ID: {bill.id}). Total: {bill.total}"
    except ValueError as e:
        return f"Validation Error: {str(e)}"
    except Exception as e:
        return f"Error approving bill: {str(e)}"

@mcp.tool()
def void_bill(id: int) -> str:
    """
    Void a bill to reverse accounting entries.
    """
    try:
        with get_db_session():
            bill = db.session.get(Bill, id)
            if not bill:
                return f"Bill with ID {id} not found."
            
            if bill.status == 'cancelled':
                return f"Bill {bill.bill_number} is already voided."
            
            bill.status = 'cancelled'
            sync_bill_gl(bill.id)
            update_vendor_balance(bill.vendor_id)
            
            return f"Successfully voided bill {bill.bill_number} (ID: {id}). Accounting entries reversed."
    except Exception as e:
        return f"Error voiding bill: {str(e)}"

@mcp.tool()
def get_unpaid_bills(vendor_id: int = None) -> str:
    """
    List unpaid bills (balance > 0).
    """
    with get_db_session():
        query = Bill.query.filter(Bill.balance > 0, Bill.status != 'draft', Bill.status != 'cancelled')
        if vendor_id:
            query = query.filter(Bill.vendor_id == vendor_id)
        
        bills = query.all()
        if not bills:
            return "No unpaid bills found."
        
        result = "Unpaid Bills:\n"
        for bill in bills:
            vendor_name = bill.vendor.name if bill.vendor else "Unknown"
            result += f"- ID: {bill.id}, Number: {bill.bill_number}, Vendor: {vendor_name}, Date: {bill.issue_date}, Total: {bill.total}, Balance: {bill.balance}, Status: {bill.status}\n"
        return result
