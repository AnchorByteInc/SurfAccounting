from flask import Blueprint, jsonify, request
from marshmallow import ValidationError
from ..extensions import db
from ..models.tax import Tax
from .schemas import tax_schema, taxes_schema

taxes_bp = Blueprint('taxes', __name__)

@taxes_bp.route('/taxes', methods=['POST'])
def create_tax():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No input data provided"}), 400
    
    try:
        new_tax = tax_schema.load(json_data)
        db.session.add(new_tax)
        db.session.commit()
        return tax_schema.jsonify(new_tax), 201
    except ValidationError as err:
        return jsonify(err.messages), 400

@taxes_bp.route('/taxes', methods=['GET'])
def get_all_taxes():
    # Filtering
    name_filter = request.args.get('name')
    is_active_filter = request.args.get('is_active')
    
    query = Tax.query
    if name_filter:
        query = query.filter(Tax.name.ilike(f'%{name_filter}%'))
    if is_active_filter:
        is_active = is_active_filter.lower() == 'true'
        query = query.filter(Tax.is_active == is_active)
        
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    # If per_page is 0 or negative, return all
    if per_page <= 0:
        taxes = query.all()
        return jsonify({
            "taxes": taxes_schema.dump(taxes),
            "total": len(taxes),
            "pages": 1,
            "current_page": 1,
            "per_page": len(taxes)
        }), 200

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    tax_items = pagination.items
    
    return jsonify({
        "taxes": taxes_schema.dump(tax_items),
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": pagination.page,
        "per_page": pagination.per_page
    }), 200

@taxes_bp.route('/taxes/<int:id>', methods=['GET'])
def get_tax(id):
    tax = Tax.query.get_or_404(id)
    return tax_schema.jsonify(tax), 200

@taxes_bp.route('/taxes/<int:id>', methods=['PUT'])
def update_tax(id):
    tax = Tax.query.get_or_404(id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No input data provided"}), 400
    
    try:
        updated_tax = tax_schema.load(json_data, instance=tax, partial=True)
        db.session.commit()
        return tax_schema.jsonify(updated_tax), 200
    except ValidationError as err:
        return jsonify(err.messages), 400

@taxes_bp.route('/taxes/<int:id>', methods=['DELETE'])
def delete_tax(id):
    tax = Tax.query.get_or_404(id)
    db.session.delete(tax)
    db.session.commit()
    return jsonify({"message": "Tax deleted"}), 200
