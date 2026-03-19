from flask import Blueprint, jsonify, request
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..models.bill import Bill, BillLine
from .schemas import bill_schema, bills_schema, bill_line_schema, bill_lines_schema
from ..services.bill_service import post_bill, sync_bill_gl

bills_bp = Blueprint('bills', __name__)

@bills_bp.route('/bills', methods=['POST'])
def create_bill():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No input data provided"}), 400
    
    try:
        new_bill = bill_schema.load(json_data)
        db.session.add(new_bill)
        db.session.commit()
        return bill_schema.jsonify(new_bill), 201
    except ValidationError as err:
        return jsonify(err.messages), 400
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"message": "Bill number already exists or integrity error", "details": str(e)}), 400

@bills_bp.route('/bills', methods=['GET'])
def get_bills():
    # Filtering
    vendor_id = request.args.get('vendor_id', type=int)
    status_filter = request.args.get('status')
    bill_number = request.args.get('bill_number')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = Bill.query
    if vendor_id:
        query = query.filter(Bill.vendor_id == vendor_id)
    if status_filter:
        query = query.filter(Bill.status == status_filter)
    if bill_number:
        query = query.filter(Bill.bill_number.ilike(f'%{bill_number}%'))
    if start_date:
        query = query.filter(Bill.issue_date >= start_date)
    if end_date:
        query = query.filter(Bill.issue_date <= end_date)
        
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    if per_page <= 0:
        bills = query.all()
        return jsonify({
            "bills": bills_schema.dump(bills),
            "total": len(bills),
            "pages": 1,
            "current_page": 1,
            "per_page": len(bills)
        }), 200

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    bills = pagination.items
    
    return jsonify({
        "bills": bills_schema.dump(bills),
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": pagination.page,
        "per_page": pagination.per_page
    }), 200

@bills_bp.route('/bills/<int:id>', methods=['GET'])
def get_bill(id):
    bill = Bill.query.get_or_404(id)
    return bill_schema.jsonify(bill), 200

@bills_bp.route('/bills/<int:id>', methods=['PUT'])
def update_bill(id):
    bill = Bill.query.get_or_404(id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No input data provided"}), 400
    
    try:
        # load(instance=bill) will update the existing object
        updated_bill = bill_schema.load(json_data, instance=bill, partial=True)
        
        # If the bill is approved, sync GL
        if updated_bill.status in ['approved', 'paid', 'overdue']:
            sync_bill_gl(updated_bill.id)
            
        db.session.commit()
        return bill_schema.jsonify(updated_bill), 200
    except ValidationError as err:
        return jsonify(err.messages), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Bill number already exists"}), 400

@bills_bp.route('/bills/<int:id>', methods=['DELETE'])
def delete_bill(id):
    bill = Bill.query.get_or_404(id)
    db.session.delete(bill)
    db.session.commit()
    return jsonify({"message": "Bill deleted"}), 200

@bills_bp.route('/bills/<int:id>/post', methods=['POST'])
def post_bill_endpoint(id):
    try:
        bill = post_bill(id)
        db.session.commit()
        return bill_schema.jsonify(bill), 200
    except ValidationError as err:
        return jsonify(err.messages), 400
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"message": "Integrity error", "details": str(e)}), 400

@bills_bp.route('/bills/status', methods=['GET'])
def status():
    return jsonify({"status": "bills blueprint active"}), 200

# --- BillLine Routes ---

@bills_bp.route('/bill_lines', methods=['POST'])
def create_bill_line():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No input data provided"}), 400
    
    try:
        new_line = bill_line_schema.load(json_data)
        db.session.add(new_line)
        
        # If the bill is approved, sync GL
        if new_line.bill and new_line.bill.status in ['approved', 'paid', 'overdue']:
            sync_bill_gl(new_line.bill.id)
            
        db.session.commit()
        return bill_line_schema.jsonify(new_line), 201
    except ValidationError as err:
        return jsonify(err.messages), 400
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"message": "Integrity error", "details": str(e)}), 400

@bills_bp.route('/bill_lines', methods=['GET'])
def get_bill_lines():
    # Filtering
    bill_id = request.args.get('bill_id', type=int)
    account_id = request.args.get('account_id', type=int)
    description = request.args.get('description')
    
    query = BillLine.query
    if bill_id:
        query = query.filter(BillLine.bill_id == bill_id)
    if account_id:
        query = query.filter(BillLine.account_id == account_id)
    if description:
        query = query.filter(BillLine.description.ilike(f'%{description}%'))
        
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    if per_page <= 0:
        lines = query.all()
        return jsonify({
            "bill_lines": bill_lines_schema.dump(lines),
            "total": len(lines),
            "pages": 1,
            "current_page": 1,
            "per_page": len(lines)
        }), 200

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    lines = pagination.items
    
    return jsonify({
        "bill_lines": bill_lines_schema.dump(lines),
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": pagination.page,
        "per_page": pagination.per_page
    }), 200

@bills_bp.route('/bill_lines/<int:id>', methods=['GET'])
def get_bill_line(id):
    line = BillLine.query.get_or_404(id)
    return bill_line_schema.jsonify(line), 200

@bills_bp.route('/bill_lines/<int:id>', methods=['PUT'])
def update_bill_line(id):
    line = BillLine.query.get_or_404(id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No input data provided"}), 400
    
    try:
        updated_line = bill_line_schema.load(json_data, instance=line, partial=True)
        
        # If the bill is approved, sync GL
        if updated_line.bill and updated_line.bill.status in ['approved', 'paid', 'overdue']:
            sync_bill_gl(updated_line.bill.id)
            
        db.session.commit()
        return bill_line_schema.jsonify(updated_line), 200
    except ValidationError as err:
        return jsonify(err.messages), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Integrity error"}), 400

@bills_bp.route('/bill_lines/<int:id>', methods=['DELETE'])
def delete_bill_line(id):
    line = BillLine.query.get_or_404(id)
    bill_id = line.bill_id
    bill_status = line.bill.status if line.bill else None
    
    db.session.delete(line)
    
    # If the bill is approved, sync GL
    if bill_id and bill_status in ['approved', 'paid', 'overdue']:
        sync_bill_gl(bill_id)
        
    db.session.commit()
    return jsonify({"message": "Bill line deleted"}), 200
