from mcp_server.tools.customers import (
    get_customers,
    get_customer,
    create_customer,
    update_customer,
    delete_customer
)
from mcp_server.schemas import CustomerCreateSchema

def test_create_customer():
    schema = CustomerCreateSchema(name="Test Customer", email="test@example.com")
    result = create_customer(schema)
    assert "Successfully created customer 'Test Customer'" in result
    assert "ID" in result

def test_get_customers():
    # Setup
    schema = CustomerCreateSchema(name="Alice")
    create_customer(schema)
    schema = CustomerCreateSchema(name="Bob")
    create_customer(schema)
    
    result = get_customers()
    assert "Alice" in result
    assert "Bob" in result
    
    result = get_customers(name_filter="Alice")
    assert "Alice" in result
    assert "Bob" not in result

def test_get_customer():
    schema = CustomerCreateSchema(name="Single Customer")
    create_customer(schema)
    # The ID should be 1 since it's the first in a fresh db
    result = get_customer(1)
    assert "Single Customer" in result

def test_update_customer():
    schema = CustomerCreateSchema(name="Old Name")
    create_customer(schema)
    
    result = update_customer(1, name="New Name")
    assert "Successfully updated" in result
    
    details = get_customer(1)
    assert "New Name" in details

def test_delete_customer():
    schema = CustomerCreateSchema(name="To Delete")
    create_customer(schema)
    
    result = delete_customer(1)
    assert "Successfully deleted" in result
    
    result = get_customer(1)
    assert "not found" in result
