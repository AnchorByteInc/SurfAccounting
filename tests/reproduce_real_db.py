from backend.app import create_app
from backend.extensions import db
from backend.models.item import Item
from flask_jwt_extended import create_access_token
import json

app = create_app()
with app.app_context():
    token = create_access_token(identity='test-user')
    headers = {
        'Authorization': f'Bearer {token}',
        'Content-Type': 'application/json'
    }
    
    payload = {
        "name":"Test Item",
        "description":"Testing Item",
        "price":100,
        "sellable":True,
        "income_account_id":10,
        "purchaseable":True,
        "expense_account_id":19,
        "sales_tax_ids":[1]
    }
    
    with app.test_client() as client:
        # Check if items with the same name already exist to avoid duplicate issues
        # But name is not unique in schema
        
        response = client.post('/api/items', json=payload, headers=headers)
        print(f"Status: {response.status_code}")
        print(f"Body: {response.get_data(as_text=True)}")
        
        # We don't want to mess up the real DB permanently, so let's rollback if possible
        # But commit() is called in the view, so it's already committed.
        # We can delete it if it succeeded.
        if response.status_code == 201:
            item_data = response.get_json()
            item_id = item_data.get('id')
            if item_id:
                item = db.session.get(Item, item_id)
                if item:
                    db.session.delete(item)
                    db.session.commit()
                    print(f"Cleaned up item {item_id}")
