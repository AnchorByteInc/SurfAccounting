from flask import Blueprint, jsonify
from sqlalchemy import func
from datetime import date, timedelta
from ..extensions import db
from ..models.invoice import Invoice
from ..models.bill import Bill
from ..models.account import Account
from ..models.journal import JournalEntryLine
from decimal import Decimal

dashboard_bp = Blueprint('dashboard', __name__)

@dashboard_bp.route('/dashboard', methods=['GET'])
def get_dashboard_data():
    # 8.1.2 Calculate revenue metric (Current Month)
    today = date.today()
    first_day_current_month = date(today.year, today.month, 1)
    
    current_month_revenue = db.session.query(func.sum(Invoice.total)).filter(
        Invoice.issue_date >= first_day_current_month,
        Invoice.status != 'cancelled'
    ).scalar() or Decimal('0.0')

    # 8.1.3 Calculate expenses metric (Current Month)
    current_month_expenses = db.session.query(func.sum(Bill.total)).filter(
        Bill.issue_date >= first_day_current_month,
        Bill.status != 'cancelled'
    ).scalar() or Decimal('0.0')

    # 8.1.4 Calculate net income
    net_income = current_month_revenue - current_month_expenses

    # 8.1.5 Calculate outstanding A/R
    outstanding_ar = db.session.query(func.sum(Invoice.balance)).filter(
        Invoice.status != 'cancelled',
        Invoice.status != 'paid'
    ).scalar() or Decimal('0.0')

    # 8.1.6 Calculate outstanding A/P
    outstanding_ap = db.session.query(func.sum(Bill.balance)).filter(
        Bill.status != 'cancelled',
        Bill.status != 'paid'
    ).scalar() or Decimal('0.0')

    # 8.1.7 Calculate cash balance
    # Sum of balances of all Asset accounts with Bank or Cash subtype
    cash_accounts = Account.query.filter(
        Account.type == 'Asset',
        Account.subtype.in_(['Bank', 'Cash'])
    ).all()
    
    total_cash_balance = Decimal('0.0')
    for account in cash_accounts:
        debits = db.session.query(func.sum(JournalEntryLine.debit)).filter(
            JournalEntryLine.account_id == account.id
        ).scalar() or Decimal('0.0')
        credits = db.session.query(func.sum(JournalEntryLine.credit)).filter(
            JournalEntryLine.account_id == account.id
        ).scalar() or Decimal('0.0')
        total_cash_balance += (debits - credits)

    # 8.1.9 Add charts for monthly revenue and expenses (Last 6 months)
    monthly_data = []
    for i in range(5, -1, -1):
        month_date = first_day_current_month - timedelta(days=i*30) # Rough approximation
        month_start = date(month_date.year, month_date.month, 1)
        if month_start.month == 12:
            month_end = date(month_start.year + 1, 1, 1) - timedelta(days=1)
        else:
            month_end = date(month_start.year, month_start.month + 1, 1) - timedelta(days=1)
            
        rev = db.session.query(func.sum(Invoice.total)).filter(
            Invoice.issue_date >= month_start,
            Invoice.issue_date <= month_end,
            Invoice.status != 'cancelled'
        ).scalar() or Decimal('0.0')
        
        exp = db.session.query(func.sum(Bill.total)).filter(
            Bill.issue_date >= month_start,
            Bill.issue_date <= month_end,
            Bill.status != 'cancelled'
        ).scalar() or Decimal('0.0')
        
        monthly_data.append({
            "month": month_start.strftime('%b %Y'),
            "revenue": float(rev),
            "expenses": float(exp)
        })

    return jsonify({
        "metrics": {
            "revenue": float(current_month_revenue),
            "expenses": float(current_month_expenses),
            "net_income": float(net_income),
            "outstanding_ar": float(outstanding_ar),
            "outstanding_ap": float(outstanding_ap),
            "cash_balance": float(total_cash_balance)
        },
        "monthly_data": monthly_data
    }), 200

@dashboard_bp.route('/dashboard/status', methods=['GET'])
def status():
    return jsonify({"status": "dashboard blueprint active"}), 200
