from flask import Blueprint, jsonify, request
from datetime import date
from ..services import report_service

reports_bp = Blueprint('reports', __name__)

@reports_bp.route('/reports/income-statement', methods=['GET'])
def income_statement():
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    if not start_date_str or not end_date_str:
        return jsonify({"message": "start_date and end_date are required"}), 400
        
    try:
        start_date = date.fromisoformat(start_date_str)
        end_date = date.fromisoformat(end_date_str)
    except ValueError:
        return jsonify({"message": "Invalid date format. Use YYYY-MM-DD"}), 400
        
    report = report_service.get_income_statement(start_date, end_date)
    return jsonify(report), 200

@reports_bp.route('/reports/profit-loss', methods=['GET'])
def profit_loss():
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    if not start_date_str or not end_date_str:
        return jsonify({"message": "start_date and end_date are required"}), 400
        
    try:
        start_date = date.fromisoformat(start_date_str)
        end_date = date.fromisoformat(end_date_str)
    except ValueError:
        return jsonify({"message": "Invalid date format. Use YYYY-MM-DD"}), 400
        
    report = report_service.get_profit_loss(start_date, end_date)
    return jsonify(report), 200

@reports_bp.route('/reports/balance-sheet', methods=['GET'])
def balance_sheet():
    as_of_date_str = request.args.get('as_of_date')
    
    if not as_of_date_str:
        as_of_date = date.today()
    else:
        try:
            as_of_date = date.fromisoformat(as_of_date_str)
        except ValueError:
            return jsonify({"message": "Invalid date format. Use YYYY-MM-DD"}), 400
            
    report = report_service.get_balance_sheet(as_of_date)
    return jsonify(report), 200

@reports_bp.route('/reports/cash-flow', methods=['GET'])
def cash_flow():
    start_date_str = request.args.get('start_date')
    end_date_str = request.args.get('end_date')
    
    if not start_date_str or not end_date_str:
        return jsonify({"message": "start_date and end_date are required"}), 400
        
    try:
        start_date = date.fromisoformat(start_date_str)
        end_date = date.fromisoformat(end_date_str)
    except ValueError:
        return jsonify({"message": "Invalid date format. Use YYYY-MM-DD"}), 400
        
    report = report_service.get_cash_flow(start_date, end_date)
    return jsonify(report), 200

@reports_bp.route('/reports/ar-aging', methods=['GET'])
def ar_aging():
    as_of_date_str = request.args.get('as_of_date')
    
    if not as_of_date_str:
        as_of_date = date.today()
    else:
        try:
            as_of_date = date.fromisoformat(as_of_date_str)
        except ValueError:
            return jsonify({"message": "Invalid date format. Use YYYY-MM-DD"}), 400
            
    report = report_service.get_ar_aging(as_of_date)
    return jsonify(report), 200

@reports_bp.route('/reports/ap-aging', methods=['GET'])
def ap_aging():
    as_of_date_str = request.args.get('as_of_date')
    
    if not as_of_date_str:
        as_of_date = date.today()
    else:
        try:
            as_of_date = date.fromisoformat(as_of_date_str)
        except ValueError:
            return jsonify({"message": "Invalid date format. Use YYYY-MM-DD"}), 400
            
    report = report_service.get_ap_aging(as_of_date)
    return jsonify(report), 200

@reports_bp.route('/reports/integrity-check', methods=['GET'])
def integrity_check():
    """12.3.1 Create balance verification dashboard (integrity checks)"""
    report = report_service.get_integrity_check()
    return jsonify(report), 200
