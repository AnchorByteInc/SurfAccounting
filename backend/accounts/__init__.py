from flask import Blueprint, jsonify, request
import csv
import io
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..models.account import Account
from .schemas import account_schema, accounts_schema

accounts_bp = Blueprint('accounts', __name__)

@accounts_bp.route('/accounts', methods=['POST'])
def create_account():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No input data provided"}), 400

    try:
        new_account = account_schema.load(json_data)
        db.session.add(new_account)
        db.session.commit()
        return account_schema.jsonify(new_account), 201
    except ValidationError as err:
        return jsonify(err.messages), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Account code already exists"}), 400

@accounts_bp.route('/accounts', methods=['GET'])
def get_accounts():
    # Filtering
    name_filter = request.args.get('name')
    code_filter = request.args.get('code')
    type_filter = request.args.get('type')
    subtype_filter = request.args.get('subtype')
    is_active_param = request.args.get('is_active')
    parent_id = request.args.get('parent_id', type=int)

    query = Account.query
    if name_filter:
        query = query.filter(Account.name.ilike(f'%{name_filter}%'))
    if code_filter:
        query = query.filter(Account.code.ilike(f'%{code_filter}%'))
    if type_filter:
        if type_filter.lower() == 'revenue':
            query = query.filter(Account.type.ilike('Revenue') | Account.type.ilike('Income'))
        elif type_filter.lower() == 'expense':
            query = query.filter(Account.type.ilike('Expense') | Account.type.ilike('Expenses') | Account.type.ilike('Cost of Goods Sold'))
        elif type_filter.lower() == 'payment':
            query = query.filter(
                (Account.type.ilike('Asset') & (
                    Account.subtype.ilike('Bank') | 
                    Account.subtype.ilike('Cash%') | 
                    Account.subtype.ilike('Savings') | 
                    Account.subtype.ilike('Chequing') |
                    Account.subtype.ilike('Undeposited Funds')
                )) |
                (Account.type.ilike('Liability') & Account.subtype.ilike('Credit Card'))
            )
        else:
            query = query.filter(Account.type.ilike(type_filter))
    if subtype_filter:
        query = query.filter(Account.subtype.ilike(f'%{subtype_filter}%'))
    if is_active_param is not None:
        if is_active_param.lower() in ['true', '1', 'yes']:
            query = query.filter(Account.is_active.is_(True))
        elif is_active_param.lower() in ['false', '0', 'no']:
            query = query.filter(Account.is_active.is_(False))
    if parent_id is not None:
        query = query.filter(Account.parent_id == parent_id)

    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    # If per_page is 0 or negative, return all
    if per_page <= 0:
        accounts = query.all()
        return jsonify({
            "accounts": accounts_schema.dump(accounts),
            "total": len(accounts),
            "pages": 1,
            "current_page": 1,
            "per_page": len(accounts)
        }), 200

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    accounts = pagination.items

    return jsonify({
        "accounts": accounts_schema.dump(accounts),
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": pagination.page,
        "per_page": pagination.per_page
    }), 200

@accounts_bp.route('/accounts/<int:id>', methods=['GET'])
def get_account(id):
    account = Account.query.get_or_404(id)
    return account_schema.jsonify(account), 200

@accounts_bp.route('/accounts/<int:id>', methods=['PUT'])
def update_account(id):
    account = Account.query.get_or_404(id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No input data provided"}), 400

    try:
        updated_account = account_schema.load(json_data, instance=account, partial=True)
        db.session.commit()
        return account_schema.jsonify(updated_account), 200
    except ValidationError as err:
        return jsonify(err.messages), 400
    except IntegrityError:
        db.session.rollback()
        return jsonify({"message": "Account code already exists"}), 400

@accounts_bp.route('/accounts/<int:id>', methods=['DELETE'])
def delete_account(id):
    account = Account.query.get_or_404(id)
    if account.is_system:
        return jsonify({"message": "Cannot delete system account"}), 400
    db.session.delete(account)
    db.session.commit()
    return jsonify({"message": "Account deleted"}), 200

@accounts_bp.route('/accounts/status', methods=['GET'])
def status():
    return jsonify({"status": "accounts blueprint active"}), 200

@accounts_bp.route('/accounts/bulk-import', methods=['POST'])
def bulk_import_accounts():
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
        
        type_mapping = {
            'Bank': 'Asset',
            'Accounts Receivable': 'Asset',
            'Current Assets': 'Asset',
            'Property, Plant & Equipment': 'Asset',
            'Accounts Payable': 'Liability',
            'Credit Card': 'Liability',
            'Other Current Liabilities': 'Liability',
            'Long-term Liabilities': 'Liability',
            'Equity': 'Equity',
            'Income': 'Revenue',
            'Cost of Goods Sold': 'Expense',
            'Expenses': 'Expense'
        }
        
        for i, row in enumerate(reader):
            try:
                name = row.get('name')
                code = row.get('code')
                account_type = row.get('type')
                
                if not name or not code or not account_type:
                    errors.append(f"Row {i+1}: Missing required fields (name, code, type)")
                    continue

                # Normalize account type
                if account_type in type_mapping:
                    if not row.get('subtype'):
                        row['subtype'] = account_type
                    account_type = type_mapping[account_type]
                
                parent_id = None
                parent_code = row.get('parent_code')
                if parent_code:
                    parent = Account.query.filter_by(code=parent_code).first()
                    if parent:
                        parent_id = parent.id
                    else:
                        # Optional: search in the current session if we want to support hierarchy in one go
                        pass

                new_account = Account(
                    name=name,
                    code=code,
                    type=account_type,
                    subtype=row.get('subtype'),
                    parent_id=parent_id,
                    is_active=row.get('is_active', 'true').lower() == 'true'
                )
                db.session.add(new_account)
                count += 1
            except Exception as e:
                errors.append(f"Row {i+1}: {str(e)}")
        
        db.session.commit()
        return jsonify({
            "message": f"Successfully imported {count} accounts",
            "count": count,
            "errors": errors
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error processing CSV: {str(e)}"}), 500
