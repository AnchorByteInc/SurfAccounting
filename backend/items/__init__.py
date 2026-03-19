from flask import Blueprint, jsonify, request
import csv
import io
from marshmallow import ValidationError
from ..extensions import db
from ..models.item import Item
from ..models.account import Account
from .schemas import item_schema, items_schema

items_bp = Blueprint('items', __name__)

@items_bp.route('/items', methods=['POST'])
def create_item():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No input data provided"}), 400
    
    try:
        new_item = item_schema.load(json_data)
        db.session.add(new_item)
        db.session.commit()
        return item_schema.jsonify(new_item), 201
    except ValidationError as err:
        return jsonify(err.messages), 400

@items_bp.route('/items', methods=['GET'])
def get_all_items():
    name_filter = request.args.get('name')
    sellable_filter = request.args.get('sellable')
    purchaseable_filter = request.args.get('purchaseable')
    
    query = Item.query
    if name_filter:
        query = query.filter(Item.name.ilike(f'%{name_filter}%'))
    if sellable_filter:
        query = query.filter(Item.sellable == (sellable_filter.lower() == 'true'))
    if purchaseable_filter:
        query = query.filter(Item.purchaseable == (purchaseable_filter.lower() == 'true'))
        
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    if per_page <= 0:
        items = query.all()
        return jsonify({
            "items": items_schema.dump(items),
            "total": len(items),
            "pages": 1,
            "current_page": 1,
            "per_page": len(items)
        }), 200

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    item_list = pagination.items
    
    return jsonify({
        "items": items_schema.dump(item_list),
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": pagination.page,
        "per_page": pagination.per_page
    }), 200

@items_bp.route('/items/<int:id>', methods=['GET'])
def get_item(id):
    item = Item.query.get_or_404(id)
    return item_schema.jsonify(item), 200

@items_bp.route('/items/<int:id>', methods=['PUT'])
def update_item(id):
    item = Item.query.get_or_404(id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No input data provided"}), 400
    
    try:
        updated_item = item_schema.load(json_data, instance=item, partial=True)
        db.session.commit()
        return item_schema.jsonify(updated_item), 200
    except ValidationError as err:
        return jsonify(err.messages), 400

@items_bp.route('/items/<int:id>', methods=['DELETE'])
def delete_item(id):
    item = Item.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "Item deleted"}), 200

@items_bp.route('/items/bulk-import', methods=['POST'])
def bulk_import_items():
    if 'file' not in request.files:
        return jsonify({"message": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400
    
    if not file.filename.endswith('.csv'):
        return jsonify({"message": "File must be a CSV"}), 400

    try:
        content = file.stream.read().decode("utf-8-sig")
        stream = io.StringIO(content, newline=None)
        reader = csv.DictReader(stream)
        
        # Normalize headers: lowercase, strip, and replace spaces with underscores
        if reader.fieldnames:
            reader.fieldnames = [f.strip().lower().replace(' ', '_') for f in reader.fieldnames]
        
        count = 0
        errors = []
        
        for i, row in enumerate(reader):
            try:
                name = row.get('name')
                if not name:
                    errors.append(f"Row {i+1}: Missing required field (name)")
                    continue
                
                income_account_id = None
                income_account_code = row.get('income_account_code')
                if income_account_code:
                    acc = Account.query.filter_by(code=income_account_code).first()
                    if acc:
                        income_account_id = acc.id
                
                expense_account_id = None
                expense_account_code = row.get('expense_account_code')
                if expense_account_code:
                    acc = Account.query.filter_by(code=expense_account_code).first()
                    if acc:
                        expense_account_id = acc.id

                new_item = Item(
                    name=name,
                    description=row.get('description') or None,
                    price=float(row.get('price', 0.0) or 0.0),
                    sellable=row.get('sellable', 'true').lower() == 'true',
                    income_account_id=income_account_id,
                    purchaseable=row.get('purchaseable', 'false').lower() == 'true',
                    expense_account_id=expense_account_id
                )
                db.session.add(new_item)
                count += 1
            except Exception as e:
                errors.append(f"Row {i+1}: {str(e)}")
        
        db.session.commit()
        return jsonify({
            "message": f"Successfully imported {count} products & services",
            "count": count,
            "errors": errors
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error processing CSV: {str(e)}"}), 500
