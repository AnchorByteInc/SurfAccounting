from flask import Blueprint, jsonify, request
import csv
import io
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..models.vendor import Vendor
from .schemas import vendor_schema, vendors_schema

vendors_bp = Blueprint('vendors', __name__)

@vendors_bp.route('/vendors', methods=['POST'])
def create_vendor():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No input data provided"}), 400
    
    try:
        new_vendor = vendor_schema.load(json_data)
        db.session.add(new_vendor)
        db.session.commit()
        return vendor_schema.jsonify(new_vendor), 201
    except ValidationError as err:
        return jsonify(err.messages), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Email already exists"}), 400

@vendors_bp.route('/vendors', methods=['GET'])
def get_vendors():
    # Filtering
    name_filter = request.args.get('name')
    email_filter = request.args.get('email')
    
    query = Vendor.query
    if name_filter:
        query = query.filter(Vendor.name.ilike(f'%{name_filter}%'))
    if email_filter:
        query = query.filter(Vendor.email.ilike(f'%{email_filter}%'))
        
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    if per_page <= 0:
        vendors = query.all()
        return jsonify({
            "vendors": vendors_schema.dump(vendors),
            "total": len(vendors),
            "pages": 1,
            "current_page": 1,
            "per_page": len(vendors)
        }), 200

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    vendors = pagination.items
    
    return jsonify({
        "vendors": vendors_schema.dump(vendors),
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": pagination.page,
        "per_page": pagination.per_page
    }), 200

@vendors_bp.route('/vendors/<int:id>', methods=['GET'])
def get_vendor(id):
    vendor = Vendor.query.get_or_404(id)
    return vendor_schema.jsonify(vendor), 200

@vendors_bp.route('/vendors/<int:id>', methods=['PUT'])
def update_vendor(id):
    vendor = Vendor.query.get_or_404(id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No input data provided"}), 400
    
    try:
        updated_vendor = vendor_schema.load(json_data, instance=vendor, partial=True)
        db.session.commit()
        return vendor_schema.jsonify(updated_vendor), 200
    except ValidationError as err:
        return jsonify(err.messages), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Email already exists"}), 400

@vendors_bp.route('/vendors/<int:id>', methods=['DELETE'])
def delete_vendor(id):
    vendor = Vendor.query.get_or_404(id)
    db.session.delete(vendor)
    db.session.commit()
    return jsonify({"message": "Vendor deleted"}), 200

@vendors_bp.route('/vendors/status', methods=['GET'])
def status():
    return jsonify({"status": "vendors blueprint active"}), 200

@vendors_bp.route('/vendors/bulk-import', methods=['POST'])
def bulk_import_vendors():
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
                
                new_vendor = Vendor(
                    name=name,
                    primary_contact_name=row.get('primary_contact_name') or None,
                    email=row.get('email') or None,
                    phone=row.get('phone') or None,
                    address=row.get('address') or None
                )
                db.session.add(new_vendor)
                count += 1
            except Exception as e:
                errors.append(f"Row {i+1}: {str(e)}")
        
        db.session.commit()
        return jsonify({
            "message": f"Successfully imported {count} vendors",
            "count": count,
            "errors": errors
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error processing CSV: {str(e)}"}), 500
