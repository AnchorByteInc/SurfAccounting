from mcp_server.tools.vendors import (
    get_vendors,
    get_vendor,
    create_vendor,
    update_vendor,
    delete_vendor
)
from mcp_server.schemas import VendorCreateSchema

def test_create_vendor():
    schema = VendorCreateSchema(name="Test Vendor", email="vendor@example.com")
    result = create_vendor(schema)
    assert "Successfully created vendor 'Test Vendor'" in result
    assert "ID" in result

def test_get_vendors():
    create_vendor(VendorCreateSchema(name="Vendor A"))
    create_vendor(VendorCreateSchema(name="Vendor B"))
    
    result = get_vendors()
    assert "Vendor A" in result
    assert "Vendor B" in result
    
    result = get_vendors(name_filter="Vendor A")
    assert "Vendor A" in result
    assert "Vendor B" not in result

def test_get_vendor():
    create_vendor(VendorCreateSchema(name="Single Vendor"))
    result = get_vendor(1)
    assert "Single Vendor" in result

def test_update_vendor():
    create_vendor(VendorCreateSchema(name="Old Vendor"))
    
    result = update_vendor(1, name="New Vendor")
    assert "Successfully updated" in result
    
    details = get_vendor(1)
    assert "New Vendor" in details

def test_delete_vendor():
    create_vendor(VendorCreateSchema(name="To Delete"))
    
    result = delete_vendor(1)
    assert "Successfully deleted" in result
    
    result = get_vendor(1)
    assert "not found" in result
