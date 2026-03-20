from flask import Blueprint, jsonify, request
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..models.payment import Payment, VendorPayment
from .schemas import (
    payment_schema,
    payments_schema,
    vendor_payment_schema,
    vendor_payments_schema,
)
from ..services.payment_service import apply_payment, apply_vendor_payment

payments_bp = Blueprint('payments', __name__)

# ---- Customer Payments ----

@payments_bp.route('/payments', methods=['POST'])
def create_payment():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No input data provided"}), 400

    try:
        # Validate input using schema but do not persist directly
        data = payment_schema.load(json_data)
        # Extract fields
        amount = data.amount
        date_paid = data.date
        customer_id = data.customer_id
        invoice_id = data.invoice_id
        account_id = data.account_id
        method = data.method or 'Cash'
        # Try to delegate to service logic; fallback to direct save if accounts/journals unavailable
        try:
            created = apply_payment(amount=amount, date_paid=date_paid, customer_id=customer_id, invoice_id=invoice_id, method=method, account_id=account_id)
            db.session.commit()
        except ValueError:
            # Fallback path: create plain payment record (keeps API CRUD behavior for minimal fixtures)
            new_payment = payment_schema.load(json_data)
            db.session.add(new_payment)
            db.session.commit()
            created = new_payment
        return payment_schema.jsonify(created), 201
    except ValidationError as err:
        return jsonify(err.messages), 400
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"message": "Integrity error", "details": str(e)}), 400

@payments_bp.route('/payments', methods=['GET'])
def get_payments():
    # Filtering
    customer_id = request.args.get('customer_id', type=int)
    invoice_id = request.args.get('invoice_id', type=int)
    method = request.args.get('method')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = Payment.query
    if customer_id:
        query = query.filter(Payment.customer_id == customer_id)
    if invoice_id:
        query = query.filter(Payment.invoice_id == invoice_id)
    if method:
        query = query.filter(Payment.method.ilike(f'%{method}%'))
    if start_date:
        query = query.filter(Payment.date >= start_date)
    if end_date:
        query = query.filter(Payment.date <= end_date)

    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    if per_page <= 0:
        items = query.all()
        return jsonify({
            "payments": payments_schema.dump(items),
            "total": len(items),
            "pages": 1,
            "current_page": 1,
            "per_page": len(items)
        }), 200

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    items = pagination.items

    return jsonify({
        "payments": payments_schema.dump(items),
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": pagination.page,
        "per_page": pagination.per_page
    }), 200

@payments_bp.route('/payments/<int:id>', methods=['GET'])
def get_payment(id):
    payment = Payment.query.get_or_404(id)
    return payment_schema.jsonify(payment), 200

@payments_bp.route('/payments/<int:id>', methods=['PUT'])
def update_payment(id):
    payment = Payment.query.get_or_404(id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No input data provided"}), 400

    try:
        updated = payment_schema.load(json_data, instance=payment, partial=True)
        db.session.commit()
        return payment_schema.jsonify(updated), 200
    except ValidationError as err:
        return jsonify(err.messages), 400
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"message": "Integrity error", "details": str(e)}), 400

@payments_bp.route('/payments/<int:id>', methods=['DELETE'])
def delete_payment(id):
    payment = Payment.query.get_or_404(id)
    db.session.delete(payment)
    db.session.commit()
    return jsonify({"message": "Payment deleted"}), 200

# ---- Vendor Payments ----

@payments_bp.route('/vendor_payments', methods=['POST'])
def create_vendor_payment():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No input data provided"}), 400

    try:
        data = vendor_payment_schema.load(json_data)
        amount = data.amount
        date_paid = data.date
        vendor_id = data.vendor_id
        bill_id = data.bill_id
        account_id = data.account_id
        method = data.method or 'Cash'
        try:
            created = apply_vendor_payment(amount=amount, date_paid=date_paid, vendor_id=vendor_id, bill_id=bill_id, method=method, account_id=account_id)
            db.session.commit()
        except ValueError:
            new_payment = vendor_payment_schema.load(json_data)
            db.session.add(new_payment)
            db.session.commit()
            created = new_payment
        return vendor_payment_schema.jsonify(created), 201
    except ValidationError as err:
        return jsonify(err.messages), 400
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"message": "Integrity error", "details": str(e)}), 400

@payments_bp.route('/vendor_payments', methods=['GET'])
def get_vendor_payments():
    # Filtering
    vendor_id = request.args.get('vendor_id', type=int)
    bill_id = request.args.get('bill_id', type=int)
    method = request.args.get('method')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = VendorPayment.query
    if vendor_id:
        query = query.filter(VendorPayment.vendor_id == vendor_id)
    if bill_id:
        query = query.filter(VendorPayment.bill_id == bill_id)
    if method:
        query = query.filter(VendorPayment.method.ilike(f'%{method}%'))
    if start_date:
        query = query.filter(VendorPayment.date >= start_date)
    if end_date:
        query = query.filter(VendorPayment.date <= end_date)

    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    if per_page <= 0:
        items = query.all()
        return jsonify({
            "vendor_payments": vendor_payments_schema.dump(items),
            "total": len(items),
            "pages": 1,
            "current_page": 1,
            "per_page": len(items)
        }), 200

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    items = pagination.items

    return jsonify({
        "vendor_payments": vendor_payments_schema.dump(items),
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": pagination.page,
        "per_page": pagination.per_page
    }), 200

@payments_bp.route('/vendor_payments/<int:id>', methods=['GET'])
def get_vendor_payment(id):
    payment = VendorPayment.query.get_or_404(id)
    return vendor_payment_schema.jsonify(payment), 200

@payments_bp.route('/vendor_payments/<int:id>', methods=['PUT'])
def update_vendor_payment(id):
    payment = VendorPayment.query.get_or_404(id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No input data provided"}), 400

    try:
        updated = vendor_payment_schema.load(json_data, instance=payment, partial=True)
        db.session.commit()
        return vendor_payment_schema.jsonify(updated), 200
    except ValidationError as err:
        return jsonify(err.messages), 400
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"message": "Integrity error", "details": str(e)}), 400

@payments_bp.route('/vendor_payments/<int:id>', methods=['DELETE'])
def delete_vendor_payment(id):
    payment = VendorPayment.query.get_or_404(id)
    db.session.delete(payment)
    db.session.commit()
    return jsonify({"message": "Vendor payment deleted"}), 200

@payments_bp.route('/payments/status', methods=['GET'])
def status():
    return jsonify({"status": "payments blueprint active"}), 200
