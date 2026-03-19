from mcp_server.instance import mcp
from mcp_server.utils.db import get_db_session
from mcp_server.schemas import ItemCreateSchema
from backend.services import item_service

# --- Section 3.1: Products & Services (Items) ---

@mcp.tool()
def get_items(name_filter: str = None) -> str:
    """
    List products and services with an optional name filter.
    """
    with get_db_session():
        items = item_service.get_items(name_filter)
        if not items:
            return "No items found."
        
        result = "Items:\n"
        for item in items:
            result += f"- ID: {item.id}, Name: {item.name}, Price: {item.price}, Sellable: {item.sellable}, Purchaseable: {item.purchaseable}\n"
        return result

@mcp.tool()
def get_item(id: int) -> str:
    """
    Get detailed view of a product or service by ID.
    """
    with get_db_session():
        item = item_service.get_item_by_id(id)
        if not item:
            return f"Item with ID {id} not found."
        
        result = f"Item Details (ID: {item.id}):\n"
        result += f"- Name: {item.name}\n"
        result += f"- Description: {item.description or 'N/A'}\n"
        result += f"- Price: {item.price}\n"
        result += f"- Sellable: {item.sellable}\n"
        result += f"- Income Account ID: {item.income_account_id or 'N/A'}\n"
        result += f"- Purchaseable: {item.purchaseable}\n"
        result += f"- Expense Account ID: {item.expense_account_id or 'N/A'}\n"
        return result

@mcp.tool()
def create_item(item: ItemCreateSchema) -> str:
    """
    Create a new product or service.
    """
    try:
        with get_db_session():
            new_item = item_service.create_item(
                name=item.name,
                description=item.description,
                price=item.price,
                sellable=item.sellable,
                income_account_id=item.income_account_id,
                purchaseable=item.purchaseable,
                expense_account_id=item.expense_account_id,
                tax_ids=item.tax_ids
            )
            return f"Successfully created item '{new_item.name}' with ID {new_item.id}."
    except Exception as e:
        return f"Error creating item: {str(e)}"

@mcp.tool()
def update_item(id: int, name: str = None, description: str = None, price: float = None, sellable: bool = None, income_account_id: int = None, purchaseable: bool = None, expense_account_id: int = None) -> str:
    """
    Update an existing product or service.
    """
    updates = {}
    if name is not None: updates['name'] = name
    if description is not None: updates['description'] = description
    if price is not None: updates['price'] = price
    if sellable is not None: updates['sellable'] = sellable
    if income_account_id is not None: updates['income_account_id'] = income_account_id
    if purchaseable is not None: updates['purchaseable'] = purchaseable
    if expense_account_id is not None: updates['expense_account_id'] = expense_account_id
    
    if not updates:
        return "No valid fields provided for update."

    try:
        with get_db_session():
            item = item_service.update_item(id, **updates)
            if not item:
                return f"Item with ID {id} not found."
            return f"Successfully updated item '{item.name}' (ID: {id})."
    except Exception as e:
        return f"Error updating item: {str(e)}"

@mcp.tool()
def delete_item(id: int) -> str:
    """
    Delete a product or service.
    """
    try:
        with get_db_session():
            success = item_service.delete_item(id)
            if not success:
                return f"Item with ID {id} not found."
            return f"Successfully deleted item with ID {id}."
    except Exception as e:
        return f"Error deleting item: {str(e)}"
