from flask import Blueprint, jsonify, request
from marshmallow import ValidationError
from ..extensions import db
from ..models.accounting_period import AccountingPeriod
from .schemas import accounting_period_schema, accounting_period_list_schema

accounting_periods_bp = Blueprint('accounting_periods', __name__)

@accounting_periods_bp.route('/accounting_periods', methods=['GET'])
def get_accounting_periods():
    periods = AccountingPeriod.query.order_by(AccountingPeriod.start_date.desc()).all()
    return accounting_period_list_schema.jsonify(periods), 200

@accounting_periods_bp.route('/accounting_periods', methods=['POST'])
def create_accounting_period():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No input data provided"}), 400
    
    try:
        new_period = accounting_period_schema.load(json_data)
        db.session.add(new_period)
        db.session.commit()
        return accounting_period_schema.jsonify(new_period), 201
    except ValidationError as err:
        return jsonify(err.messages), 400

@accounting_periods_bp.route('/accounting_periods/<int:id>/close', methods=['POST'])
def close_accounting_period(id):
    period = AccountingPeriod.query.get_or_404(id)
    period.is_closed = True
    db.session.commit()
    return accounting_period_schema.jsonify(period), 200

@accounting_periods_bp.route('/accounting_periods/<int:id>', methods=['DELETE'])
def delete_accounting_period(id):
    period = AccountingPeriod.query.get_or_404(id)
    if period.is_closed:
        return jsonify({"message": "Cannot delete a closed accounting period"}), 400
    
    db.session.delete(period)
    db.session.commit()
    return jsonify({"message": "Accounting period deleted"}), 200
