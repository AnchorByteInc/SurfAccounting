from flask import Blueprint, jsonify, request
import csv
import io
from marshmallow import ValidationError
from sqlalchemy.exc import IntegrityError
from ..extensions import db
from ..models.journal import JournalEntry, JournalEntryLine
from ..models.account import Account
from .schemas import (
    journal_entry_schema,
    journal_entries_schema,
    journal_entry_line_schema,
    journal_entry_lines_schema,
)
from ..services.journal_service import validate_journal_entry
from ..utils.money import to_decimal

journals_bp = Blueprint('journals', __name__)

# --- JournalEntry Routes ---

@journals_bp.route('/journal_entries', methods=['POST'])
def create_journal_entry():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No input data provided"}), 400

    try:
        new_entry = journal_entry_schema.load(json_data)
        if not new_entry.transaction_type:
            new_entry.transaction_type = "Journal Entry"
        # Validate balance before save (also enforced by model event)
        validate_journal_entry(new_entry)
        db.session.add(new_entry)
        db.session.commit()
        return journal_entry_schema.jsonify(new_entry), 201
    except ValidationError as err:
        return jsonify(err.messages), 400
    except ValueError as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 400
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"message": "Integrity error", "details": str(e)}), 400


@journals_bp.route('/journal_entries', methods=['GET'])
def get_journal_entries():
    # Filtering
    reference = request.args.get('reference')
    memo = request.args.get('memo')
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')

    query = JournalEntry.query
    if reference:
        query = query.filter(JournalEntry.reference.ilike(f'%{reference}%'))
    if memo:
        query = query.filter(JournalEntry.memo.ilike(f'%{memo}%'))
    if start_date:
        query = query.filter(JournalEntry.date >= start_date)
    if end_date:
        query = query.filter(JournalEntry.date <= end_date)

    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    if per_page <= 0:
        entries = query.all()
        return jsonify({
            "journal_entries": journal_entries_schema.dump(entries),
            "total": len(entries),
            "pages": 1,
            "current_page": 1,
            "per_page": len(entries)
        }), 200

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    entries = pagination.items

    return jsonify({
        "journal_entries": journal_entries_schema.dump(entries),
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": pagination.page,
        "per_page": pagination.per_page
    }), 200


@journals_bp.route('/journal_entries/<int:id>', methods=['GET'])
def get_journal_entry(id):
    entry = JournalEntry.query.get_or_404(id)
    return journal_entry_schema.jsonify(entry), 200


@journals_bp.route('/journal_entries/<int:id>', methods=['PUT'])
def update_journal_entry(id):
    entry = JournalEntry.query.get_or_404(id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No input data provided"}), 400

    try:
        updated_entry = journal_entry_schema.load(json_data, instance=entry, partial=True)
        # Validate balance before commit
        validate_journal_entry(updated_entry)
        db.session.commit()
        return journal_entry_schema.jsonify(updated_entry), 200
    except ValidationError as err:
        return jsonify(err.messages), 400
    except ValueError as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 400


@journals_bp.route('/journal_entries/<int:id>', methods=['DELETE'])
def delete_journal_entry(id):
    entry = JournalEntry.query.get_or_404(id)
    db.session.delete(entry)
    db.session.commit()
    return jsonify({"message": "Journal entry deleted"}), 200


@journals_bp.route('/journal_entries/status', methods=['GET'])
def status():
    return jsonify({"status": "journals blueprint active"}), 200

@journals_bp.route('/journal_entries/bulk-import', methods=['POST'])
def bulk_import_journals():
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
        
        entries_data = {} # Keyed by (date, reference, memo, transaction_type, index)
        current_key = None
        last_key = None
        
        for i, row in enumerate(reader):
            # A row is a "header row" if it has a date
            # But we only treat it as a *new* entry if it has (date AND (reference OR memo)) 
            # OR if it's the very first row with a date.
            
            date = row.get('date')
            reference = row.get('reference', '')
            memo = row.get('memo', '')
            transaction_type = row.get('transaction_type', 'Journal Entry') or 'Journal Entry'
            
            is_new_entry = False
            if date:
                if not current_key:
                    is_new_entry = True
                else:
                    # Header fields from current entry's start row
                    curr_date, curr_ref, curr_memo, curr_ttype, _ = current_key
                    if (date != curr_date or 
                        reference != curr_ref or 
                        memo != curr_memo or 
                        transaction_type != curr_ttype):
                        is_new_entry = True
            
            if is_new_entry:
                current_key = (date, reference, memo, transaction_type, i)
            
            if not current_key:
                continue
            
            if current_key not in entries_data:
                # If we just started a new entry, we use the values from the current row
                # If the current row is a continuation row (blank date/ref/memo), 
                # we don't hit this block because it would already be in entries_data.
                # However, if we forced is_new_entry, we hit this.
                entries_data[current_key] = {
                    "date": date or entries_data.get(last_key, {}).get("date"), # Fallback for safety
                    "reference": reference or None,
                    "memo": memo or None,
                    "transaction_type": transaction_type,
                    "source_module": row.get('source_module') or None,
                    "source_id": int(row.get('source_id')) if row.get('source_id') else None,
                    "vendor_id": int(row.get('vendor_id')) if row.get('vendor_id') else None,
                    "customer_id": int(row.get('customer_id')) if row.get('customer_id') else None,
                    "lines": []
                }
                last_key = current_key
            
            account_code = row.get('account_code')
            debit = to_decimal(row.get('debit', 0.0) or 0.0)
            credit = to_decimal(row.get('credit', 0.0) or 0.0)
            description = row.get('description') or None
            
            if account_code:
                entries_data[current_key]["lines"].append({
                    "account_code": account_code,
                    "debit": debit,
                    "credit": credit,
                    "description": description
                })
        
        count = 0
        errors = []
        
        from datetime import datetime
        
        for key, data in entries_data.items():
            try:
                # Convert date string to date object
                try:
                    entry_date = datetime.strptime(data["date"], '%Y-%m-%d').date()
                except ValueError:
                    errors.append(f"Entry {data['reference']}: Invalid date format {data['date']}. Use YYYY-MM-DD")
                    continue

                new_entry = JournalEntry(
                    date=entry_date,
                    reference=data["reference"],
                    memo=data["memo"],
                    transaction_type=data.get('transaction_type', 'Journal Entry'),
                    source_module=data.get('source_module'),
                    source_id=data.get('source_id'),
                    vendor_id=data.get('vendor_id'),
                    customer_id=data.get('customer_id')
                )
                
                for line_data in data["lines"]:
                    account = Account.query.filter_by(code=line_data["account_code"]).first()
                    if not account:
                        raise ValueError(f"Account code {line_data['account_code']} not found")
                    
                    line = JournalEntryLine(
                        account_id=account.id,
                        debit=line_data["debit"],
                        credit=line_data["credit"],
                        description=line_data.get('description')
                    )
                    new_entry.lines.append(line)
                
                # Check balance
                if not new_entry.is_balanced():
                    debits = sum(to_decimal(l.debit or 0) for l in new_entry.lines)
                    credits = sum(to_decimal(l.credit or 0) for l in new_entry.lines)
                    raise ValueError(f"Journal entry {data['reference']} is not balanced (D:{debits} C:{credits})")
                
                db.session.add(new_entry)
                count += 1
            except Exception as e:
                errors.append(f"Entry {data['reference']}: {str(e)}")
        
        db.session.commit()
        return jsonify({
            "message": f"Successfully imported {count} journal entries",
            "count": count,
            "errors": errors
        }), 201
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": f"Error processing CSV: {str(e)}"}), 500


# --- JournalEntryLine Routes ---

@journals_bp.route('/journal_entry_lines', methods=['POST'])
def create_journal_entry_line():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No input data provided"}), 400

    try:
        new_line = journal_entry_line_schema.load(json_data)
        db.session.add(new_line)
        db.session.commit()
        # After adding a line to an entry, ensure the parent remains balanced on next update/save flows
        return journal_entry_line_schema.jsonify(new_line), 201
    except ValidationError as err:
        return jsonify(err.messages), 400
    except IntegrityError as e:
        db.session.rollback()
        return jsonify({"message": "Integrity error", "details": str(e)}), 400


@journals_bp.route('/journal_entry_lines', methods=['GET'])
def get_journal_entry_lines():
    # Filtering
    journal_entry_id = request.args.get('journal_entry_id', type=int)
    account_id = request.args.get('account_id', type=int)
    amount_type = request.args.get('type')  # 'debit' or 'credit'

    query = JournalEntryLine.query
    if journal_entry_id:
        query = query.filter(JournalEntryLine.journal_entry_id == journal_entry_id)
    if account_id:
        query = query.filter(JournalEntryLine.account_id == account_id)
    if amount_type == 'debit':
        query = query.filter(JournalEntryLine.debit > 0)
    if amount_type == 'credit':
        query = query.filter(JournalEntryLine.credit > 0)

    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    if per_page <= 0:
        lines = query.all()
        return jsonify({
            "journal_entry_lines": journal_entry_lines_schema.dump(lines),
            "total": len(lines),
            "pages": 1,
            "current_page": 1,
            "per_page": len(lines)
        }), 200

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    lines = pagination.items

    return jsonify({
        "journal_entry_lines": journal_entry_lines_schema.dump(lines),
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": pagination.page,
        "per_page": pagination.per_page
    }), 200


@journals_bp.route('/journal_entry_lines/<int:id>', methods=['GET'])
def get_journal_entry_line(id):
    line = JournalEntryLine.query.get_or_404(id)
    return journal_entry_line_schema.jsonify(line), 200


@journals_bp.route('/journal_entry_lines/<int:id>', methods=['PUT'])
def update_journal_entry_line(id):
    line = JournalEntryLine.query.get_or_404(id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No input data provided"}), 400

    try:
        updated_line = journal_entry_line_schema.load(json_data, instance=line, partial=True)
        db.session.commit()
        return journal_entry_line_schema.jsonify(updated_line), 200
    except ValidationError as err:
        return jsonify(err.messages), 400


@journals_bp.route('/journal_entry_lines/<int:id>', methods=['DELETE'])
def delete_journal_entry_line(id):
    line = JournalEntryLine.query.get_or_404(id)
    db.session.delete(line)
    db.session.commit()
    return jsonify({"message": "Journal entry line deleted"}), 200
