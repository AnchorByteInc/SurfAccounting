from flask import Blueprint, jsonify, request
import csv
import io
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..models.customer import Customer
from .schemas import customer_schema, customers_schema

customers_bp = Blueprint('customers', __name__)

@customers_bp.route('/customers', methods=['POST'])
def create_customer():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No input data provided"}), 400
    
    try:
        new_customer = customer_schema.load(json_data)
        db.session.add(new_customer)
        db.session.commit()
        return customer_schema.jsonify(new_customer), 201
    except ValidationError as err:
        return jsonify(err.messages), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Email already exists"}), 400

@customers_bp.route('/customers', methods=['GET'])
def get_customers():
    # Filtering
    name_filter = request.args.get('name')
    email_filter = request.args.get('email')
    
    query = Customer.query
    if name_filter:
        query = query.filter(Customer.name.ilike(f'%{name_filter}%'))
    if email_filter:
        query = query.filter(Customer.email.ilike(f'%{email_filter}%'))
        
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    if per_page <= 0:
        customers = query.all()
        return jsonify({
            "customers": customers_schema.dump(customers),
            "total": len(customers),
            "pages": 1,
            "current_page": 1,
            "per_page": len(customers)
        }), 200

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    customers = pagination.items
    
    return jsonify({
        "customers": customers_schema.dump(customers),
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": pagination.page,
        "per_page": pagination.per_page
    }), 200

@customers_bp.route('/customers/<int:id>', methods=['GET'])
def get_customer(id):
    customer = Customer.query.get_or_404(id)
    return customer_schema.jsonify(customer), 200

@customers_bp.route('/customers/<int:id>', methods=['PUT'])
def update_customer(id):
    customer = Customer.query.get_or_404(id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No input data provided"}), 400
    
    try:
        updated_customer = customer_schema.load(json_data, instance=customer, partial=True)
        db.session.commit()
        return customer_schema.jsonify(updated_customer), 200
    except ValidationError as err:
        return jsonify(err.messages), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Email already exists"}), 400

@customers_bp.route('/customers/<int:id>', methods=['DELETE'])
def delete_customer(id):
    customer = Customer.query.get_or_404(id)
    db.session.delete(customer)
    db.session.commit()
    return jsonify({"message": "Customer deleted"}), 200

@customers_bp.route('/customers/status', methods=['GET'])
def status():
    return jsonify({"status": "customers blueprint active"}), 200

@customers_bp.route('/customers/bulk-import', methods=['POST'])
def bulk_import_customers():
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
                
                new_customer = Customer(
                    name=name,
                    primary_contact_name=row.get('primary_contact_name') or None,
                    email=row.get('email') or None,
                    phone=row.get('phone') or None,
                    website=row.get('website') or None,
                    billing_address=(row.get('billing_address') or row.get('address')) or None,
                    shipping_address=row.get('shipping_address') or None
                )
                db.session.add(new_customer)
                count += 1
            except Exception as e:
                errors.append(f"Row {i+1}: {str(e)}")
        
        db.session.commit()
        return jsonify({
            "message": f"Successfully imported {count} customers",
            "count": count,
            "errors": errors
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error processing CSV: {str(e)}"}), 500
