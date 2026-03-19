from mcp_server.instance import mcp
from mcp_server.utils.db import get_db_session
from mcp_server.schemas import VendorCreateSchema
from backend.extensions import db
from backend.models import Vendor

# --- Section 2.2: Vendor Management Tools ---

@mcp.tool()
def get_vendors(name_filter: str = None) -> str:
    """
    List vendors with an optional name filter for lookup and listing.
    """
    with get_db_session():
        query = Vendor.query
        if name_filter:
            query = query.filter(Vendor.name.ilike(f'%{name_filter}%'))
        
        vendors = query.all()
        if not vendors:
            return "No vendors found."
        
        result = "Vendors:\n"
        for v in vendors:
            result += f"- ID: {v.id}, Name: {v.name}, Email: {v.email or 'N/A'}, Balance: {v.balance}\n"
        return result

@mcp.tool()
def get_vendor(id: int) -> str:
    """
    Get detailed view of a vendor by ID.
    """
    with get_db_session():
        vendor = db.session.get(Vendor, id)
        if not vendor:
            return f"Vendor with ID {id} not found."
        
        result = f"Vendor Details (ID: {vendor.id}):\n"
        result += f"- Name: {vendor.name}\n"
        result += f"- Contact: {vendor.primary_contact_name or 'N/A'}\n"
        result += f"- Email: {vendor.email or 'N/A'}\n"
        result += f"- Phone: {vendor.phone or 'N/A'}\n"
        result += f"- Address: {vendor.address or 'N/A'}\n"
        result += f"- Balance: {vendor.balance}\n"
        return result

@mcp.tool()
def create_vendor(vendor: VendorCreateSchema) -> str:
    """
    Create a new vendor record.
    """
    try:
        with get_db_session():
            new_vendor = Vendor(
                name=vendor.name,
                email=vendor.email,
                phone=vendor.phone,
                primary_contact_name=vendor.primary_contact_name,
                address=vendor.address
            )
            db.session.add(new_vendor)
            db.session.flush() # To get the ID
            return f"Successfully created vendor '{new_vendor.name}' with ID {new_vendor.id}."
    except Exception as e:
        return f"Error creating vendor: {str(e)}"

@mcp.tool()
def update_vendor(id: int, name: str = None, email: str = None, phone: str = None, primary_contact_name: str = None, address: str = None) -> str:
    """
    Update an existing vendor record by ID.
    """
    updates = {}
    if name is not None: updates['name'] = name
    if email is not None: updates['email'] = email
    if phone is not None: updates['phone'] = phone
    if primary_contact_name is not None: updates['primary_contact_name'] = primary_contact_name
    if address is not None: updates['address'] = address
    
    if not updates:
        return "No valid fields provided for update."

    try:
        with get_db_session():
            vendor = db.session.get(Vendor, id)
            if not vendor:
                return f"Vendor with ID {id} not found."
            
            for key, value in updates.items():
                setattr(vendor, key, value)
                
            return f"Successfully updated vendor '{vendor.name}' (ID: {id})."
    except Exception as e:
        return f"Error updating vendor: {str(e)}"

@mcp.tool()
def delete_vendor(id: int) -> str:
    """
    Delete a vendor record by ID, checking for related transactions.
    """
    from sqlalchemy.exc import IntegrityError
    try:
        with get_db_session():
            vendor = db.session.get(Vendor, id)
            if not vendor:
                return f"Vendor with ID {id} not found."
            
            try:
                db.session.delete(vendor)
                db.session.flush()
                return f"Successfully deleted vendor with ID {id}."
            except IntegrityError:
                db.session.rollback()
                return f"Cannot delete vendor (ID: {id}) because they have related transactions or records."
    except Exception as e:
        return f"Error deleting vendor: {str(e)}"
