from flask import Blueprint, jsonify, request
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..models.invoice import Invoice, InvoiceLine
from .schemas import invoice_schema, invoices_schema, invoice_line_schema, invoice_lines_schema
from ..services.invoice_service import post_invoice

invoices_bp = Blueprint('invoices', __name__)

@invoices_bp.route('/invoices', methods=['POST'])
def create_invoice():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No input data provided"}), 400
    
    try:
        new_invoice = invoice_schema.load(json_data)
        db.session.add(new_invoice)
        db.session.commit()
        return invoice_schema.jsonify(new_invoice), 201
    except ValidationError as err:
        return jsonify(err.messages), 400
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"message": "Invoice number already exists or integrity error", "details": str(e)}), 400

@invoices_bp.route('/invoices', methods=['GET'])
def get_invoices():
    # Filtering
    customer_id = request.args.get('customer_id', type=int)
    status_filter = request.args.get('status')
    invoice_number = request.args.get('invoice_number')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    
    query = Invoice.query
    if customer_id:
        query = query.filter(Invoice.customer_id == customer_id)
    if status_filter:
        query = query.filter(Invoice.status == status_filter)
    if invoice_number:
        query = query.filter(Invoice.invoice_number.ilike(f'%{invoice_number}%'))
    if start_date:
        query = query.filter(Invoice.issue_date >= start_date)
    if end_date:
        query = query.filter(Invoice.issue_date <= end_date)
        
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    if per_page <= 0:
        invoices = query.all()
        return jsonify({
            "invoices": invoices_schema.dump(invoices),
            "total": len(invoices),
            "pages": 1,
            "current_page": 1,
            "per_page": len(invoices)
        }), 200

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    invoices = pagination.items
    
    return jsonify({
        "invoices": invoices_schema.dump(invoices),
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": pagination.page,
        "per_page": pagination.per_page
    }), 200

@invoices_bp.route('/invoices/<int:id>', methods=['GET'])
def get_invoice(id):
    invoice = Invoice.query.get_or_404(id)
    return invoice_schema.jsonify(invoice), 200

@invoices_bp.route('/invoices/<int:id>', methods=['PUT'])
def update_invoice(id):
    invoice = Invoice.query.get_or_404(id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No input data provided"}), 400
    
    try:
        # load(instance=invoice) will update the existing object
        updated_invoice = invoice_schema.load(json_data, instance=invoice, partial=True)
        db.session.commit()
        return invoice_schema.jsonify(updated_invoice), 200
    except ValidationError as err:
        return jsonify(err.messages), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Invoice number already exists"}), 400

@invoices_bp.route('/invoices/<int:id>', methods=['DELETE'])
def delete_invoice(id):
    invoice = Invoice.query.get_or_404(id)
    db.session.delete(invoice)
    db.session.commit()
    return jsonify({"message": "Invoice deleted"}), 200

@invoices_bp.route('/invoices/<int:id>/post', methods=['POST'])
def post_invoice_endpoint(id):
    try:
        invoice = post_invoice(id)
        db.session.commit()
        return invoice_schema.jsonify(invoice), 200
    except ValidationError as err:
        return jsonify(err.messages), 400
    except ValueError as e:
        return jsonify({"message": str(e)}), 400
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"message": "Integrity error", "details": str(e)}), 400

@invoices_bp.route('/invoices/status', methods=['GET'])
def status():
    return jsonify({"status": "invoices blueprint active"}), 200

# --- InvoiceLine Routes ---

@invoices_bp.route('/invoice_lines', methods=['POST'])
def create_invoice_line():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No input data provided"}), 400
    
    try:
        new_line = invoice_line_schema.load(json_data)
        db.session.add(new_line)
        db.session.commit()
        return invoice_line_schema.jsonify(new_line), 201
    except ValidationError as err:
        return jsonify(err.messages), 400
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"message": "Integrity error", "details": str(e)}), 400

@invoices_bp.route('/invoice_lines', methods=['GET'])
def get_invoice_lines():
    # Filtering
    invoice_id = request.args.get('invoice_id', type=int)
    account_id = request.args.get('account_id', type=int)
    description = request.args.get('description')
    
    query = InvoiceLine.query
    if invoice_id:
        query = query.filter(InvoiceLine.invoice_id == invoice_id)
    if account_id:
        query = query.filter(InvoiceLine.account_id == account_id)
    if description:
        query = query.filter(InvoiceLine.description.ilike(f'%{description}%'))
        
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    if per_page <= 0:
        lines = query.all()
        return jsonify({
            "invoice_lines": invoice_lines_schema.dump(lines),
            "total": len(lines),
            "pages": 1,
            "current_page": 1,
            "per_page": len(lines)
        }), 200

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    lines = pagination.items
    
    return jsonify({
        "invoice_lines": invoice_lines_schema.dump(lines),
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": pagination.page,
        "per_page": pagination.per_page
    }), 200

@invoices_bp.route('/invoice_lines/<int:id>', methods=['GET'])
def get_invoice_line(id):
    line = InvoiceLine.query.get_or_404(id)
    return invoice_line_schema.jsonify(line), 200

@invoices_bp.route('/invoice_lines/<int:id>', methods=['PUT'])
def update_invoice_line(id):
    line = InvoiceLine.query.get_or_404(id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No input data provided"}), 400
    
    try:
        updated_line = invoice_line_schema.load(json_data, instance=line, partial=True)
        db.session.commit()
        return invoice_line_schema.jsonify(updated_line), 200
    except ValidationError as err:
        return jsonify(err.messages), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Integrity error"}), 400

@invoices_bp.route('/invoice_lines/<int:id>', methods=['DELETE'])
def delete_invoice_line(id):
    line = InvoiceLine.query.get_or_404(id)
    db.session.delete(line)
    db.session.commit()
    return jsonify({"message": "Invoice line deleted"}), 200
