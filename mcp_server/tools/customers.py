from mcp_server.instance import mcp
from mcp_server.utils.db import get_db_session
from mcp_server.schemas import CustomerCreateSchema
from backend.extensions import db
from backend.models import Customer

# --- Section 2.1: Customer Management Tools ---

@mcp.tool()
def get_customers(name_filter: str = None) -> str:
    """
    List customers with an optional name filter for lookup and listing.
    """
    with get_db_session():
        query = Customer.query
        if name_filter:
            query = query.filter(Customer.name.ilike(f'%{name_filter}%'))
        
        customers = query.all()
        if not customers:
            return "No customers found."
        
        result = "Customers:\n"
        for c in customers:
            result += f"- ID: {c.id}, Name: {c.name}, Email: {c.email or 'N/A'}, Balance: {c.balance}\n"
        return result

@mcp.tool()
def get_customer(id: int) -> str:
    """
    Get detailed view of a customer by ID.
    """
    with get_db_session():
        customer = db.session.get(Customer, id)
        if not customer:
            return f"Customer with ID {id} not found."
        
        result = f"Customer Details (ID: {customer.id}):\n"
        result += f"- Name: {customer.name}\n"
        result += f"- Contact: {customer.primary_contact_name or 'N/A'}\n"
        result += f"- Email: {customer.email or 'N/A'}\n"
        result += f"- Phone: {customer.phone or 'N/A'}\n"
        result += f"- Website: {customer.website or 'N/A'}\n"
        result += f"- Billing Address: {customer.billing_address or 'N/A'}\n"
        result += f"- Shipping Address: {customer.shipping_address or 'N/A'}\n"
        result += f"- Balance: {customer.balance}\n"
        return result

@mcp.tool()
def create_customer(customer: CustomerCreateSchema) -> str:
    """
    Create a new customer record.
    """
    try:
        with get_db_session():
            new_customer = Customer(
                name=customer.name,
                email=customer.email,
                phone=customer.phone,
                primary_contact_name=customer.primary_contact_name,
                website=customer.website,
                billing_address=customer.billing_address,
                shipping_address=customer.shipping_address
            )
            db.session.add(new_customer)
            db.session.flush() # To get the ID
            return f"Successfully created customer '{new_customer.name}' with ID {new_customer.id}."
    except Exception as e:
        return f"Error creating customer: {str(e)}"

@mcp.tool()
def update_customer(id: int, name: str = None, email: str = None, phone: str = None, primary_contact_name: str = None, website: str = None, billing_address: str = None, shipping_address: str = None) -> str:
    """
    Update an existing customer record by ID.
    """
    updates = {}
    if name is not None:
        updates['name'] = name
    if email is not None:
        updates['email'] = email
    if phone is not None:
        updates['phone'] = phone
    if primary_contact_name is not None:
        updates['primary_contact_name'] = primary_contact_name
    if website is not None:
        updates['website'] = website
    if billing_address is not None:
        updates['billing_address'] = billing_address
    if shipping_address is not None:
        updates['shipping_address'] = shipping_address
    
    if not updates:
        return "No valid fields provided for update."

    try:
        with get_db_session():
            customer = db.session.get(Customer, id)
            if not customer:
                return f"Customer with ID {id} not found."
            
            for key, value in updates.items():
                setattr(customer, key, value)
                
            return f"Successfully updated customer '{customer.name}' (ID: {id})."
    except Exception as e:
        return f"Error updating customer: {str(e)}"

@mcp.tool()
def delete_customer(id: int) -> str:
    """
    Delete a customer record by ID, checking for related transactions.
    """
    from sqlalchemy.exc import IntegrityError
    try:
        with get_db_session():
            customer = db.session.get(Customer, id)
            if not customer:
                return f"Customer with ID {id} not found."
            
            try:
                db.session.delete(customer)
                db.session.flush()
                return f"Successfully deleted customer with ID {id}."
            except IntegrityError:
                db.session.rollback()
                return f"Cannot delete customer (ID: {id}) because they have related transactions or invoices."
    except Exception as e:
        return f"Error deleting customer: {str(e)}"
