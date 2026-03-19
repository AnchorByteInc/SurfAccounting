from mcp_server.instance import mcp
from mcp_server.utils.db import get_db_session
from mcp_server.schemas import PaymentCreateSchema, VendorPaymentCreateSchema, PaymentDetailsSchema
from backend.services.payment_service import apply_payment, apply_vendor_payment
from backend.models.invoice import Invoice
from backend.models.bill import Bill
from backend.extensions import db

# --- Section 6.1: Financial Operations & Payments ---

@mcp.tool()
def create_customer_payment(payment_data: PaymentCreateSchema) -> str:
    """
    Create a payment from a customer. Optionally apply it to a specific invoice.
    """
    try:
        with get_db_session():
            payment = apply_payment(
                amount=payment_data.amount,
                date_paid=payment_data.date,
                customer_id=payment_data.customer_id,
                invoice_id=payment_data.invoice_id,
                method=payment_data.payment_method,
                account_id=payment_data.account_id
            )
            return f"Successfully created customer payment (ID: {payment.id}) of {payment_data.amount} for customer ID {payment_data.customer_id}."
    except Exception as e:
        return f"Error creating customer payment: {str(e)}"

@mcp.tool()
def create_vendor_payment(payment_data: VendorPaymentCreateSchema) -> str:
    """
    Create a payment to a vendor. Optionally apply it to a specific bill.
    """
    try:
        with get_db_session():
            payment = apply_vendor_payment(
                amount=payment_data.amount,
                date_paid=payment_data.date,
                vendor_id=payment_data.vendor_id,
                bill_id=payment_data.bill_id,
                method=payment_data.payment_method,
                account_id=payment_data.account_id
            )
            return f"Successfully created vendor payment (ID: {payment.id}) of {payment_data.amount} to vendor ID {payment_data.vendor_id}."
    except Exception as e:
        return f"Error creating vendor payment: {str(e)}"

@mcp.tool()
def mark_invoice_as_paid(invoice_id: int, payment_details: PaymentDetailsSchema) -> str:
    """
    Convenience tool to mark an invoice as paid by creating a payment for its full balance.
    """
    try:
        with get_db_session():
            invoice = db.session.get(Invoice, invoice_id)
            if not invoice:
                return f"Error: Invoice with ID {invoice_id} not found."
            
            amount = float(invoice.balance)
            if amount <= 0:
                return f"Invoice {invoice.invoice_number} already has a zero or negative balance ({amount})."
            
            payment = apply_payment(
                amount=amount,
                date_paid=payment_details.date,
                customer_id=invoice.customer_id,
                invoice_id=invoice_id,
                method=payment_details.payment_method or 'Cash',
                account_id=payment_details.account_id
            )
            return f"Successfully marked invoice {invoice.invoice_number} as paid with payment (ID: {payment.id}) of {amount}."
    except Exception as e:
        return f"Error marking invoice as paid: {str(e)}"

@mcp.tool()
def mark_bill_as_paid(bill_id: int, payment_details: PaymentDetailsSchema) -> str:
    """
    Convenience tool to mark a bill as paid by creating a payment for its full balance.
    """
    try:
        with get_db_session():
            bill = db.session.get(Bill, bill_id)
            if not bill:
                return f"Error: Bill with ID {bill_id} not found."
            
            amount = float(bill.balance)
            if amount <= 0:
                return f"Bill {bill.bill_number} already has a zero or negative balance ({amount})."
            
            payment = apply_vendor_payment(
                amount=amount,
                date_paid=payment_details.date,
                vendor_id=bill.vendor_id,
                bill_id=bill_id,
                method=payment_details.payment_method or 'Cash',
                account_id=payment_details.account_id
            )
            return f"Successfully marked bill {bill.bill_number} as paid with payment (ID: {payment.id}) of {amount}."
    except Exception as e:
        return f"Error marking bill as paid: {str(e)}"
