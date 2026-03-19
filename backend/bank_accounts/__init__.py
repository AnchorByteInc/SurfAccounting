from flask import Blueprint, jsonify, request
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..models.bank import BankAccount
from .schemas import bank_account_schema, bank_accounts_schema

bank_accounts_bp = Blueprint('bank_accounts', __name__)

@bank_accounts_bp.route('/bank_accounts', methods=['POST'])
def create_bank_account():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No input data provided"}), 400

    try:
        new_acc = bank_account_schema.load(json_data)
        db.session.add(new_acc)
        db.session.commit()
        return bank_account_schema.jsonify(new_acc), 201
    except ValidationError as err:
        return jsonify(err.messages), 400
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"message": "Integrity error", "details": str(e)}), 400

@bank_accounts_bp.route('/bank_accounts', methods=['GET'])
def get_bank_accounts():
    # Filtering
    name_filter = request.args.get('name')
    account_id = request.args.get('account_id', type=int)
    account_number = request.args.get('account_number')

    query = BankAccount.query
    if name_filter:
        query = query.filter(BankAccount.name.ilike(f'%{name_filter}%'))
    if account_id:
        query = query.filter(BankAccount.account_id == account_id)
    if account_number:
        query = query.filter(BankAccount.account_number.ilike(f'%{account_number}%'))

    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    if per_page <= 0:
        items = query.all()
        return jsonify({
            "bank_accounts": bank_accounts_schema.dump(items),
            "total": len(items),
            "pages": 1,
            "current_page": 1,
            "per_page": len(items)
        }), 200

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    items = pagination.items

    return jsonify({
        "bank_accounts": bank_accounts_schema.dump(items),
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": pagination.page,
        "per_page": pagination.per_page
    }), 200

@bank_accounts_bp.route('/bank_accounts/<int:id>', methods=['GET'])
def get_bank_account(id):
    item = BankAccount.query.get_or_404(id)
    return bank_account_schema.jsonify(item), 200

@bank_accounts_bp.route('/bank_accounts/<int:id>', methods=['PUT'])
def update_bank_account(id):
    item = BankAccount.query.get_or_404(id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No input data provided"}), 400

    try:
        updated = bank_account_schema.load(json_data, instance=item, partial=True)
        db.session.commit()
        return bank_account_schema.jsonify(updated), 200
    except ValidationError as err:
        return jsonify(err.messages), 400
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"message": "Integrity error", "details": str(e)}), 400

@bank_accounts_bp.route('/bank_accounts/<int:id>', methods=['DELETE'])
def delete_bank_account(id):
    item = BankAccount.query.get_or_404(id)
    db.session.delete(item)
    db.session.commit()
    return jsonify({"message": "BankAccount deleted"}), 200

@bank_accounts_bp.route('/bank_accounts/status', methods=['GET'])
def status():
    return jsonify({"status": "bank_accounts blueprint active"}), 200
