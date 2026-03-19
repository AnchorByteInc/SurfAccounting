from mcp_server.instance import mcp
from mcp_server.utils.db import get_db_session
from mcp_server.schemas import InvoiceCreateSchema
from backend.extensions import db
from backend.models import Invoice, Customer, InvoiceLine, Tax
from backend.services.invoice_service import post_invoice, update_customer_balance, sync_invoice_journal

# --- Section 4.1: Sales Workflow: Invoices ---

@mcp.tool()
def get_invoices(customer_id: int = None, status: str = None) -> str:
    """
    List invoices, optionally filtered by customer_id or status.
    """
    with get_db_session():
        query = Invoice.query
        if customer_id:
            query = query.filter(Invoice.customer_id == customer_id)
        if status:
            query = query.filter(Invoice.status == status)
        
        invoices = query.all()
        if not invoices:
            return "No invoices found."
        
        result = "Invoices:\n"
        for inv in invoices:
            customer_name = inv.customer.name if inv.customer else "Unknown"
            result += f"- ID: {inv.id}, Number: {inv.invoice_number}, Customer: {customer_name}, Date: {inv.issue_date}, Total: {inv.total}, Status: {inv.status}\n"
        return result

@mcp.tool()
def get_invoice(id: int) -> str:
    """
    Detailed view of a single invoice, including its line items.
    """
    with get_db_session():
        invoice = db.session.get(Invoice, id)
        if not invoice:
            return f"Invoice with ID {id} not found."
        
        customer_name = invoice.customer.name if invoice.customer else "Unknown"
        result = f"Invoice #{invoice.invoice_number} (ID: {invoice.id})\n"
        result += f"- Customer: {customer_name} (ID: {invoice.customer_id})\n"
        result += f"- Issue Date: {invoice.issue_date}\n"
        result += f"- Due Date: {invoice.due_date}\n"
        result += f"- Status: {invoice.status}\n"
        result += f"- Subtotal: {invoice.subtotal}\n"
        result += f"- Tax: {invoice.tax}\n"
        result += f"- Total: {invoice.total}\n"
        result += f"- Balance: {invoice.balance}\n"
        result += "\nLine Items:\n"
        
        for line in invoice.lines:
            result += f"  - {line.description or 'No description'}: {line.quantity} x {line.unit_price} = {line.line_total} (Account: {line.account.name if line.account else 'N/A'})\n"
            
        return result

@mcp.tool()
def create_invoice(invoice_data: InvoiceCreateSchema) -> str:
    """
    Create a new draft invoice.
    """
    try:
        with get_db_session():
            customer = db.session.get(Customer, invoice_data.customer_id)
            if not customer:
                return f"Error: Customer with ID {invoice_data.customer_id} not found."

            new_invoice = Invoice(
                customer_id=invoice_data.customer_id,
                issue_date=invoice_data.issue_date,
                due_date=invoice_data.due_date,
                invoice_number=invoice_data.invoice_number,
                status='draft'
            )
            
            db.session.add(new_invoice)
            db.session.flush()
            
            for line_data in invoice_data.lines:
                line = InvoiceLine(
                    item_id=line_data.item_id,
                    description=line_data.description,
                    quantity=line_data.quantity,
                    unit_price=line_data.unit_price,
                    account_id=line_data.account_id
                )
                if line_data.tax_ids:
                    line.taxes = db.session.query(Tax).filter(Tax.id.in_(line_data.tax_ids)).all()
                new_invoice.lines.append(line)
            
            db.session.flush()
            return f"Successfully created draft invoice '{new_invoice.invoice_number}' (ID: {new_invoice.id}) with {len(new_invoice.lines)} lines. Total: {new_invoice.total}"
    except Exception as e:
        return f"Error creating invoice: {str(e)}"

@mcp.tool()
def update_invoice(id: int, customer_id: int = None, issue_date: str = None, due_date: str = None, status: str = None, invoice_number: str = None) -> str:
    """
    Update a draft invoice. Only draft invoices can be updated.
    """
    from datetime import datetime
    try:
        with get_db_session():
            invoice = db.session.get(Invoice, id)
            if not invoice:
                return f"Invoice with ID {id} not found."
            
            if invoice.status != 'draft':
                return f"Cannot update invoice {invoice.invoice_number} because it is in '{invoice.status}' status (only 'draft' invoices can be updated)."
            
            updated_count = 0
            if customer_id is not None:
                invoice.customer_id = customer_id
                updated_count += 1
            if issue_date is not None:
                try:
                    invoice.issue_date = datetime.strptime(issue_date, '%Y-%m-%d').date()
                    updated_count += 1
                except ValueError:
                    return "Error: Invalid issue_date format. Use YYYY-MM-DD."
            if due_date is not None:
                try:
                    invoice.due_date = datetime.strptime(due_date, '%Y-%m-%d').date()
                    updated_count += 1
                except ValueError:
                    return "Error: Invalid due_date format. Use YYYY-MM-DD."
            if invoice_number is not None:
                invoice.invoice_number = invoice_number
                updated_count += 1
            if status is not None:
                invoice.status = status
                updated_count += 1
                
            if updated_count == 0:
                return "No valid fields provided for update."
                
            db.session.flush()
            return f"Successfully updated draft invoice {invoice.invoice_number} (ID: {id})."
    except Exception as e:
        return f"Error updating invoice: {str(e)}"

@mcp.tool()
def delete_invoice(id: int) -> str:
    """
    Delete a draft invoice. Only draft or unposted invoices can be deleted.
    """
    try:
        with get_db_session():
            invoice = db.session.get(Invoice, id)
            if not invoice:
                return f"Invoice with ID {id} not found."
            
            if invoice.status != 'draft':
                return f"Cannot delete invoice {invoice.invoice_number} because it is in '{invoice.status}' status (only 'draft' invoices can be deleted)."
            
            db.session.delete(invoice)
            return f"Successfully deleted draft invoice {invoice.invoice_number} (ID: {id})."
    except Exception as e:
        return f"Error deleting invoice: {str(e)}"

# --- Section 4.2: Invoice Processing ---

@mcp.tool()
def approve_invoice(id: int) -> str:
    """
    Approve a draft invoice, posting it to the ledger.
    """
    try:
        with get_db_session():
            invoice = post_invoice(id)
            return f"Successfully approved and posted invoice '{invoice.invoice_number}' (ID: {invoice.id}). Total: {invoice.total}"
    except ValueError as e:
        return f"Validation Error: {str(e)}"
    except Exception as e:
        return f"Error approving invoice: {str(e)}"

@mcp.tool()
def void_invoice(id: int) -> str:
    """
    Void an invoice to reverse accounting entries.
    """
    try:
        with get_db_session():
            invoice = db.session.get(Invoice, id)
            if not invoice:
                return f"Invoice with ID {id} not found."
            
            if invoice.status == 'cancelled':
                return f"Invoice {invoice.invoice_number} is already voided."
            
            invoice.status = 'cancelled'
            sync_invoice_journal(invoice, delete=True)
            update_customer_balance(invoice.customer_id)
            
            return f"Successfully voided invoice {invoice.invoice_number} (ID: {id}). Accounting entries reversed."
    except Exception as e:
        return f"Error voiding invoice: {str(e)}"

@mcp.tool()
def get_unpaid_invoices(customer_id: int = None) -> str:
    """
    List unpaid invoices (balance > 0).
    """
    with get_db_session():
        query = Invoice.query.filter(Invoice.balance > 0, Invoice.status != 'draft', Invoice.status != 'cancelled')
        if customer_id:
            query = query.filter(Invoice.customer_id == customer_id)
        
        invoices = query.all()
        if not invoices:
            return "No unpaid invoices found."
        
        result = "Unpaid Invoices:\n"
        for inv in invoices:
            customer_name = inv.customer.name if inv.customer else "Unknown"
            result += f"- ID: {inv.id}, Number: {inv.invoice_number}, Customer: {customer_name}, Date: {inv.issue_date}, Total: {inv.total}, Balance: {inv.balance}, Status: {inv.status}\n"
        return result
