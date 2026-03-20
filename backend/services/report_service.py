from datetime import date
from sqlalchemy import func
from ..extensions import db
from ..models.account import Account
from ..models.journal import JournalEntry, JournalEntryLine
from ..models.invoice import Invoice
from ..models.bill import Bill
from ..models.customer import Customer
from ..models.vendor import Vendor
from ..utils.ledger import get_account_balance
from decimal import Decimal

def get_income_statement(start_date, end_date):
    """
    7.1.1 Implement Income Statement calculation
    Revenue - Expenses for a period.
    """
    # Revenue accounts
    revenue_accounts = Account.query.filter(Account.type == 'Revenue').all()
    revenue_data = []
    total_revenue = Decimal('0.00')
    
    for acc in revenue_accounts:
        balance = db.session.query(
            func.sum(JournalEntryLine.credit) - func.sum(JournalEntryLine.debit)
        ).join(JournalEntry).filter(
            JournalEntryLine.account_id == acc.id,
            JournalEntry.date >= start_date,
            JournalEntry.date <= end_date
        ).scalar() or Decimal('0.00')
        
        if balance != 0:
            revenue_data.append({
                'account_name': f"{acc.code} {acc.name}",
                'account_code': acc.code,
                'balance': float(balance)
            })
            total_revenue += balance

    # Expense accounts
    expense_accounts = Account.query.filter(Account.type == 'Expense').all()
    expense_data = []
    total_expenses = Decimal('0.00')
    
    for acc in expense_accounts:
        balance = db.session.query(
            func.sum(JournalEntryLine.debit) - func.sum(JournalEntryLine.credit)
        ).join(JournalEntry).filter(
            JournalEntryLine.account_id == acc.id,
            JournalEntry.date >= start_date,
            JournalEntry.date <= end_date
        ).scalar() or Decimal('0.00')
        
        if balance != 0:
            expense_data.append({
                'account_name': f"{acc.code} {acc.name}",
                'account_code': acc.code,
                'balance': float(balance)
            })
            total_expenses += balance
            
    net_income = total_revenue - total_expenses
    
    return {
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'revenue': revenue_data,
        'total_revenue': float(total_revenue),
        'expenses': expense_data,
        'total_expenses': float(total_expenses),
        'net_income': float(net_income)
    }

def get_profit_loss(start_date, end_date):
    """
    7.1.2 Implement Profit & Loss calculation
    Alias for Income Statement.
    """
    return get_income_statement(start_date, end_date)

def get_balance_sheet(as_of_date):
    """
    7.1.3 Implement Balance Sheet calculation
    Assets = Liabilities + Equity at a point in time.
    """
    # Asset accounts
    asset_accounts = Account.query.filter(Account.type == 'Asset').all()
    asset_data = []
    total_assets = Decimal('0.00')
    
    for acc in asset_accounts:
        balance = db.session.query(
            func.sum(JournalEntryLine.debit) - func.sum(JournalEntryLine.credit)
        ).join(JournalEntry).filter(
            JournalEntryLine.account_id == acc.id,
            JournalEntry.date <= as_of_date
        ).scalar() or Decimal('0.00')
        
        if balance != 0:
            asset_data.append({
                'account_name': f"{acc.code} {acc.name}",
                'account_code': acc.code,
                'balance': float(balance)
            })
            total_assets += balance

    # Liability accounts
    liability_accounts = Account.query.filter(Account.type == 'Liability').all()
    liability_data = []
    total_liabilities = Decimal('0.00')
    
    for acc in liability_accounts:
        balance = db.session.query(
            func.sum(JournalEntryLine.credit) - func.sum(JournalEntryLine.debit)
        ).join(JournalEntry).filter(
            JournalEntryLine.account_id == acc.id,
            JournalEntry.date <= as_of_date
        ).scalar() or Decimal('0.00')
        
        if balance != 0:
            liability_data.append({
                'account_name': f"{acc.code} {acc.name}",
                'account_code': acc.code,
                'balance': float(balance)
            })
            total_liabilities += balance

    # Equity accounts
    equity_accounts = Account.query.filter(Account.type == 'Equity').all()
    equity_data = []
    total_equity = Decimal('0.00')
    
    for acc in equity_accounts:
        balance = db.session.query(
            func.sum(JournalEntryLine.credit) - func.sum(JournalEntryLine.debit)
        ).join(JournalEntry).filter(
            JournalEntryLine.account_id == acc.id,
            JournalEntry.date <= as_of_date
        ).scalar() or Decimal('0.00')
        
        if balance != 0:
            equity_data.append({
                'account_name': f"{acc.code} {acc.name}",
                'account_code': acc.code,
                'balance': float(balance)
            })
            total_equity += balance
            
    # Include current year earnings (Profit & Loss up to as_of_date)
    # This is required for the Balance Sheet to balance.
    # Typically, previous years' earnings are in Retained Earnings, 
    # and current year's earnings are calculated separately.
    # For simplicity, we calculate net income from all Revenue and Expense accounts up to as_of_date.
    
    revenue_balance = db.session.query(
        func.sum(JournalEntryLine.credit) - func.sum(JournalEntryLine.debit)
    ).join(JournalEntry).join(Account).filter(
        Account.type == 'Revenue',
        JournalEntry.date <= as_of_date
    ).scalar() or Decimal('0.00')
    
    expense_balance = db.session.query(
        func.sum(JournalEntryLine.debit) - func.sum(JournalEntryLine.credit)
    ).join(JournalEntry).join(Account).filter(
        Account.type == 'Expense',
        JournalEntry.date <= as_of_date
    ).scalar() or Decimal('0.00')
    
    net_income = revenue_balance - expense_balance
    total_equity += net_income
    
    if net_income != 0:
        equity_data.append({
            'account_name': 'NI Net Income',
            'account_code': 'NI',
            'balance': float(net_income)
        })

    return {
        'as_of_date': as_of_date.isoformat(),
        'assets': asset_data,
        'total_assets': float(total_assets),
        'liabilities': liability_data,
        'total_liabilities': float(total_liabilities),
        'equity': equity_data,
        'total_equity': float(total_equity)
    }

def get_cash_flow(start_date, end_date):
    """
    7.1.4 Implement Statement of Cash Flows
    Simplified version: Net change in cash accounts during the period.
    Better version would categorize by Operating, Investing, Financing activities.
    """
    # Cash accounts
    cash_accounts = Account.query.filter(
        (Account.type == 'Asset') & (
            Account.subtype.ilike('Bank') | 
            Account.subtype.ilike('Cash%') | 
            Account.subtype.ilike('Savings') | 
            Account.subtype.ilike('Chequing') |
            Account.subtype.ilike('Undeposited Funds')
        )
    ).all()
    
    # For a truly simplified Cash Flow statement, we'll just show the movement in Cash accounts.
    # But a real one starts with Net Income and adjusts for non-cash items.
    
    # We'll do a simple "Net Change in Cash" approach.
    starting_cash_total = Decimal('0.00')
    for acc in cash_accounts:
        starting_balance = db.session.query(
            func.sum(JournalEntryLine.debit) - func.sum(JournalEntryLine.credit)
        ).join(JournalEntry).filter(
            JournalEntryLine.account_id == acc.id,
            JournalEntry.date < start_date
        ).scalar() or Decimal('0.00')
        starting_cash_total += starting_balance

    ending_cash_total = Decimal('0.00')
    for acc in cash_accounts:
        ending_balance = db.session.query(
            func.sum(JournalEntryLine.debit) - func.sum(JournalEntryLine.credit)
        ).join(JournalEntry).filter(
            JournalEntryLine.account_id == acc.id,
            JournalEntry.date <= end_date
        ).scalar() or Decimal('0.00')
        ending_cash_total += ending_balance

    # Very basic categorization
    # Net Income (Operating)
    revenue_balance = db.session.query(
        func.sum(JournalEntryLine.credit) - func.sum(JournalEntryLine.debit)
    ).join(JournalEntry).join(Account).filter(
        Account.type == 'Revenue',
        JournalEntry.date >= start_date,
        JournalEntry.date <= end_date
    ).scalar() or Decimal('0.00')
    
    expense_balance = db.session.query(
        func.sum(JournalEntryLine.debit) - func.sum(JournalEntryLine.credit)
    ).join(JournalEntry).join(Account).filter(
        Account.type == 'Expense',
        JournalEntry.date >= start_date,
        JournalEntry.date <= end_date
    ).scalar() or Decimal('0.00')
    
    net_income = revenue_balance - expense_balance
    
    # Adjust for changes in A/R and A/P (Indirect method)
    # Change in Operating Assets (A/R, Inventory, etc.)
    operating_asset_subtypes = ['Accounts Receivable%', 'Inventory', 'Prepaid Expenses']
    ar_accounts = Account.query.filter(
        db.or_(*[Account.subtype.ilike(s) for s in operating_asset_subtypes])
    ).all()
    
    ar_breakdown = []
    change_in_ar = Decimal('0.00')
    for acc in ar_accounts:
        start_bal = db.session.query(
            func.sum(JournalEntryLine.debit) - func.sum(JournalEntryLine.credit)
        ).join(JournalEntry).filter(
            JournalEntryLine.account_id == acc.id,
            JournalEntry.date < start_date
        ).scalar() or Decimal('0.00')
        
        end_bal = db.session.query(
            func.sum(JournalEntryLine.debit) - func.sum(JournalEntryLine.credit)
        ).join(JournalEntry).filter(
            JournalEntryLine.account_id == acc.id,
            JournalEntry.date <= end_date
        ).scalar() or Decimal('0.00')
        
        change = end_bal - start_bal
        if change != 0:
            ar_breakdown.append({
                'id': acc.id,
                'name': f"{acc.code} {acc.name}",
                'code': acc.code,
                'change': float(-change) # Increase in asset is decrease in cash
            })
            change_in_ar += change
    
    # Change in Operating Liabilities (A/P, Credit Cards, etc.)
    operating_liability_subtypes = ['Accounts Payable%', 'Credit Card', 'GST/HST Payable', 'Payroll Liabilities']
    ap_accounts = Account.query.filter(
        db.or_(*[Account.subtype.ilike(s) for s in operating_liability_subtypes])
    ).all()
    
    ap_breakdown = []
    change_in_ap = Decimal('0.00')
    for acc in ap_accounts:
        start_bal = db.session.query(
            func.sum(JournalEntryLine.credit) - func.sum(JournalEntryLine.debit)
        ).join(JournalEntry).filter(
            JournalEntryLine.account_id == acc.id,
            JournalEntry.date < start_date
        ).scalar() or Decimal('0.00')
        
        end_bal = db.session.query(
            func.sum(JournalEntryLine.credit) - func.sum(JournalEntryLine.debit)
        ).join(JournalEntry).filter(
            JournalEntryLine.account_id == acc.id,
            JournalEntry.date <= end_date
        ).scalar() or Decimal('0.00')
        
        change = end_bal - start_bal
        if change != 0:
            ap_breakdown.append({
                'id': acc.id,
                'name': f"{acc.code} {acc.name}",
                'code': acc.code,
                'change': float(change) # Increase in liability is increase in cash
            })
            change_in_ap += change
    
    # Non-cash adjustments (Amortization)
    amort_start = db.session.query(
        func.sum(JournalEntryLine.credit) - func.sum(JournalEntryLine.debit)
    ).join(JournalEntry).join(Account).filter(
        Account.subtype.ilike('Accumulated Amortization'),
        JournalEntry.date < start_date
    ).scalar() or Decimal('0.00')
    
    amort_end = db.session.query(
        func.sum(JournalEntryLine.credit) - func.sum(JournalEntryLine.debit)
    ).join(JournalEntry).join(Account).filter(
        Account.subtype.ilike('Accumulated Amortization'),
        JournalEntry.date <= end_date
    ).scalar() or Decimal('0.00')
    
    change_in_amort = amort_end - amort_start
    
    operating_activities = net_income - change_in_ar + change_in_ap + change_in_amort
    
    # Investing Activities (Fixed Assets)
    investing_subtypes = ['Machinery and Equipment', 'Furniture and Fixtures', 'Leasehold Improvements']
    inv_start = db.session.query(
        func.sum(JournalEntryLine.debit) - func.sum(JournalEntryLine.credit)
    ).join(JournalEntry).join(Account).filter(
        db.or_(*[Account.subtype.ilike(s) for s in investing_subtypes]),
        JournalEntry.date < start_date
    ).scalar() or Decimal('0.00')
    
    inv_end = db.session.query(
        func.sum(JournalEntryLine.debit) - func.sum(JournalEntryLine.credit)
    ).join(JournalEntry).join(Account).filter(
        db.or_(*[Account.subtype.ilike(s) for s in investing_subtypes]),
        JournalEntry.date <= end_date
    ).scalar() or Decimal('0.00')
    
    net_investing_cash = -(inv_end - inv_start) # Increase in asset is decrease in cash
    
    # Financing Activities (Loans and Equity)
    financing_subtypes = [
        'Bank Loans', 'Partner Contributions', 'Partner Distributions', 
        'Accumulated Adjustment', 'Opening Balance Equity'
    ]
    fin_accounts = Account.query.filter(
        db.or_(*[Account.subtype.ilike(s) for s in financing_subtypes])
    ).all()
    
    financing_breakdown = []
    net_financing_cash = Decimal('0.00')
    for acc in fin_accounts:
        start_bal = db.session.query(
            func.sum(JournalEntryLine.credit) - func.sum(JournalEntryLine.debit)
        ).join(JournalEntry).filter(
            JournalEntryLine.account_id == acc.id,
            JournalEntry.date < start_date
        ).scalar() or Decimal('0.00')
        
        end_bal = db.session.query(
            func.sum(JournalEntryLine.credit) - func.sum(JournalEntryLine.debit)
        ).join(JournalEntry).filter(
            JournalEntryLine.account_id == acc.id,
            JournalEntry.date <= end_date
        ).scalar() or Decimal('0.00')
        
        change = end_bal - start_bal
        if change != 0:
            financing_breakdown.append({
                'id': acc.id,
                'name': f"{acc.code} {acc.name}",
                'code': acc.code,
                'change': float(change)
            })
            net_financing_cash += change
    
    return {
        'start_date': start_date.isoformat(),
        'end_date': end_date.isoformat(),
        'starting_cash': float(starting_cash_total),
        'net_income': float(net_income),
        'change_in_ar': float(-change_in_ar),
        'ar_breakdown': ar_breakdown,
        'change_in_ap': float(change_in_ap),
        'ap_breakdown': ap_breakdown,
        'change_in_amort': float(change_in_amort),
        'net_operating_cash': float(operating_activities),
        'net_investing_cash': float(net_investing_cash),
        'net_financing_cash': float(net_financing_cash),
        'financing_breakdown': financing_breakdown,
        'ending_cash': float(ending_cash_total),
        'net_change_in_cash': float(ending_cash_total - starting_cash_total)
    }

def get_ar_aging(as_of_date):
    """
    7.1.5 Implement A/R Aging report
    Unpaid invoices grouped by age.
    """
    invoices = Invoice.query.filter(
        Invoice.balance > 0,
        Invoice.issue_date <= as_of_date,
        Invoice.status != 'cancelled'
    ).all()
    
    aging = {
        'current': 0.0,
        '1-30': 0.0,
        '31-60': 0.0,
        '61-90': 0.0,
        '90+': 0.0,
        'total': 0.0
    }
    
    customers_aging = {}
    
    for inv in invoices:
        days_overdue = (as_of_date - inv.due_date).days
        amount = float(inv.balance)
        
        if inv.customer_id not in customers_aging:
            customers_aging[inv.customer_id] = {
                'customer_name': inv.customer.name,
                'current': 0.0,
                '1-30': 0.0,
                '31-60': 0.0,
                '61-90': 0.0,
                '90+': 0.0,
                'total': 0.0
            }
            
        bucket = ''
        if days_overdue <= 0:
            bucket = 'current'
        elif days_overdue <= 30:
            bucket = '1-30'
        elif days_overdue <= 60:
            bucket = '31-60'
        elif days_overdue <= 90:
            bucket = '61-90'
        else:
            bucket = '90+'
            
        aging[bucket] += amount
        aging['total'] += amount
        customers_aging[inv.customer_id][bucket] += amount
        customers_aging[inv.customer_id]['total'] += amount
        
    return {
        'as_of_date': as_of_date.isoformat(),
        'summary': aging,
        'by_customer': list(customers_aging.values())
    }

def get_ap_aging(as_of_date):
    """
    7.1.6 Implement A/P Aging report
    Unpaid bills grouped by age.
    """
    bills = Bill.query.filter(
        Bill.balance > 0,
        Bill.issue_date <= as_of_date,
        Bill.status != 'cancelled'
    ).all()
    
    aging = {
        'current': 0.0,
        '1-30': 0.0,
        '31-60': 0.0,
        '61-90': 0.0,
        '90+': 0.0,
        'total': 0.0
    }
    
    vendors_aging = {}
    
    for bill in bills:
        days_overdue = (as_of_date - bill.due_date).days
        amount = float(bill.balance)
        
        if bill.vendor_id not in vendors_aging:
            vendors_aging[bill.vendor_id] = {
                'vendor_name': bill.vendor.name,
                'current': 0.0,
                '1-30': 0.0,
                '31-60': 0.0,
                '61-90': 0.0,
                '90+': 0.0,
                'total': 0.0
            }
            
        bucket = ''
        if days_overdue <= 0:
            bucket = 'current'
        elif days_overdue <= 30:
            bucket = '1-30'
        elif days_overdue <= 60:
            bucket = '31-60'
        elif days_overdue <= 90:
            bucket = '61-90'
        else:
            bucket = '90+'
            
        aging[bucket] += amount
        aging['total'] += amount
        vendors_aging[bill.vendor_id][bucket] += amount
        vendors_aging[bill.vendor_id]['total'] += amount
        
    return {
        'as_of_date': as_of_date.isoformat(),
        'summary': aging,
        'by_vendor': list(vendors_aging.values())
    }

def get_integrity_check():
    """
    12.3.1 Create balance verification dashboard (integrity checks)
    Performs multiple accounting integrity checks.
    """
    # 1. Trial Balance Check: sum(debit - credit) for all JournalEntryLine
    trial_balance_sum = db.session.query(
        func.coalesce(func.sum(JournalEntryLine.debit - JournalEntryLine.credit), 0)
    ).scalar()
    trial_balance_balanced = Decimal(str(trial_balance_sum)).quantize(Decimal('0.0001')) == Decimal('0.0000')

    # 2. Balance Sheet Integrity: Assets = Liabilities + Equity
    bs = get_balance_sheet(date.today())
    # total_assets, total_liabilities, total_equity are floats in get_balance_sheet
    balance_sheet_balanced = abs(bs['total_assets'] - (bs['total_liabilities'] + bs['total_equity'])) < 0.001

    # 3. AR Subsidiary Ledger Check
    total_customer_balance = db.session.query(func.sum(Customer.balance)).scalar() or Decimal('0.00')
    ar_account = Account.query.filter_by(subtype='Accounts Receivable').first()
    if not ar_account:
        ar_account = Account.query.filter_by(code='1200').first()
    
    ar_gl_balance = Decimal('0.00')
    if ar_account:
        ar_gl_balance = get_account_balance(ar_account.id)
    
    ar_subsidiary_ledger_match = Decimal(str(total_customer_balance)).quantize(Decimal('0.01')) == ar_gl_balance.quantize(Decimal('0.01'))

    # 4. AP Subsidiary Ledger Check
    total_vendor_balance = db.session.query(func.sum(Vendor.balance)).scalar() or Decimal('0.00')
    ap_account = Account.query.filter_by(subtype='Accounts Payable').first()
    if not ap_account:
        ap_account = Account.query.filter_by(code='2000').first()
        
    ap_gl_balance = Decimal('0.00')
    if ap_account:
        ap_gl_balance = get_account_balance(ap_account.id)
    
    # AP GL balance is usually credit, so it's negative (debit-credit).
    # Vendor balance is positive (credit).
    ap_subsidiary_ledger_match = Decimal(str(total_vendor_balance)).quantize(Decimal('0.01')) == (-ap_gl_balance).quantize(Decimal('0.01'))

    # 5. Unbalanced Journal Entries
    # Filter only those that are NOT balanced
    all_jes = JournalEntry.query.all()
    unbalanced_jes = []
    for je in all_jes:
        if not je.is_balanced():
            unbalanced_jes.append({
                "id": je.id,
                "date": je.date.isoformat(),
                "reference": je.reference,
                "memo": je.memo
            })
    
    return {
        "trial_balance": {
            "status": "pass" if trial_balance_balanced else "fail",
            "sum": float(trial_balance_sum)
        },
        "balance_sheet": {
            "status": "pass" if balance_sheet_balanced else "fail",
            "assets": bs['total_assets'],
            "liabilities": bs['total_liabilities'],
            "equity": bs['total_equity'],
            "difference": float(abs(Decimal(str(bs['total_assets'])) - (Decimal(str(bs['total_liabilities'])) + Decimal(str(bs['total_equity'])))))
        },
        "ar_subsidiary": {
            "status": "pass" if ar_subsidiary_ledger_match else "fail",
            "customer_total": float(total_customer_balance),
            "gl_balance": float(ar_gl_balance)
        },
        "ap_subsidiary": {
            "status": "pass" if ap_subsidiary_ledger_match else "fail",
            "vendor_total": float(total_vendor_balance),
            "gl_balance": float(ap_gl_balance)
        },
        "journal_entries": {
            "status": "pass" if not unbalanced_jes else "fail",
            "unbalanced_count": len(unbalanced_jes),
            "unbalanced_details": unbalanced_jes
        }
    }
