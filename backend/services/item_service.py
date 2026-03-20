from ..extensions import db
from ..models.item import Item

def get_items(name_filter=None):
    query = Item.query
    if name_filter:
        query = query.filter(Item.name.ilike(f'%{name_filter}%'))
    return query.all()

def get_item_by_id(item_id):
    return db.session.get(Item, item_id)

def create_item(name, income_account_id=None, expense_account_id=None, description=None, price=0.0, sellable=True, purchaseable=False, tax_ids=None):
    from ..models.tax import Tax
    item = Item(
        name=name,
        description=description,
        price=price,
        sellable=sellable,
        income_account_id=income_account_id,
        purchaseable=purchaseable,
        expense_account_id=expense_account_id
    )
    if tax_ids:
        taxes = Tax.query.filter(Tax.id.in_(tax_ids)).all()
        item.sales_taxes = taxes
    db.session.add(item)
    return item

def update_item(item_id, **updates):
    item = db.session.get(Item, item_id)
    if not item:
        return None
    
    for key, value in updates.items():
        if hasattr(item, key):
            setattr(item, key, value)
            
    return item

def delete_item(item_id):
    item = db.session.get(Item, item_id)
    if not item:
        return False
    
    # TODO: check for related transactions if necessary
    db.session.delete(item)
    return True
