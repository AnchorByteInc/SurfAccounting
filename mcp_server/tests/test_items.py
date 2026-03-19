from mcp_server.tools.items import (
    get_items,
    get_item,
    create_item,
    update_item,
    delete_item
)
from mcp_server.schemas import ItemCreateSchema
from backend.models.account import Account
from backend.extensions import db

def test_create_item():
    # Setup accounts
    income_acc = Account(name="Sales", code="4000", type="Revenue")
    db.session.add(income_acc)
    db.session.commit()
    
    schema = ItemCreateSchema(
        name="Test Item",
        price=10.0,
        income_account_id=income_acc.id
    )
    result = create_item(schema)
    assert "Successfully created item 'Test Item'" in result

def test_get_items():
    create_item(ItemCreateSchema(name="Item A"))
    create_item(ItemCreateSchema(name="Item B"))
    
    result = get_items()
    assert "Item A" in result
    assert "Item B" in result
    
    result = get_items(name_filter="Item A")
    assert "Item A" in result
    assert "Item B" not in result

def test_get_item():
    create_item(ItemCreateSchema(name="Single Item"))
    # ID should be 3 because of previous tests in this file (if not for clean_db)
    # But clean_db runs before each test, so it should be 1.
    result = get_item(1)
    assert "Single Item" in result

def test_update_item():
    create_item(ItemCreateSchema(name="Old Item"))
    
    result = update_item(1, name="New Item", price=20.0)
    assert "Successfully updated" in result
    
    details = get_item(1)
    assert "New Item" in details
    assert "20.0" in details

def test_delete_item():
    create_item(ItemCreateSchema(name="To Delete"))
    
    result = delete_item(1)
    assert "Successfully deleted" in result
    
    result = get_item(1)
    assert "not found" in result
