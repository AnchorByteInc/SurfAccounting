import pytest
from datetime import date
from backend.app import create_app
from backend.config import Config
from backend.extensions import db
from backend.models.account import Account
from backend.models.journal import JournalEntry, JournalEntryLine
from backend.services.report_service import get_cash_flow
from decimal import Decimal

class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True

@pytest.fixture
def app():
    app = create_app(TestConfig)
    
    with app.app_context():
        db.create_all()
        # Seed necessary accounts
        bank = Account(name='Bank', code='1000', type='Asset', subtype='Bank')
        savings = Account(name='Savings', code='1058', type='Asset', subtype='Savings')
        ar = Account(name='Accounts Receivable (A/R)', code='1200', type='Asset', subtype='Accounts Receivable (A/R)')
        ap = Account(name='Accounts Payable (A/P)', code='2000', type='Liability', subtype='Accounts Payable (A/P)')
        revenue = Account(name='Sales', code='4000', type='Revenue', subtype='Revenue')
        
        db.session.add_all([bank, savings, ar, ap, revenue])
        db.session.commit()
        
        yield app
        db.session.remove()
        db.drop_all()

def test_cash_flow_ar_change(app):
    with app.app_context():
        bank = Account.query.filter_by(code='1000').first()
        ar = Account.query.filter_by(code='1200').first()
        revenue = Account.query.filter_by(code='4000').first()
        
        # Transaction 1: Invoice (Debit AR, Credit Revenue) - Jan 15 2025
        je1 = JournalEntry(date=date(2025, 1, 15), memo='Invoice 1')
        db.session.add(je1)
        db.session.flush()
        db.session.add(JournalEntryLine(journal_entry_id=je1.id, account_id=ar.id, debit=Decimal('100.00'), credit=0))
        db.session.add(JournalEntryLine(journal_entry_id=je1.id, account_id=revenue.id, debit=0, credit=Decimal('100.00')))
        
        # Transaction 2: Payment (Debit Bank, Credit AR) - Feb 15 2025
        je2 = JournalEntry(date=date(2025, 2, 15), memo='Payment 1')
        db.session.add(je2)
        db.session.flush()
        db.session.add(JournalEntryLine(journal_entry_id=je2.id, account_id=bank.id, debit=Decimal('40.00'), credit=0))
        db.session.add(JournalEntryLine(journal_entry_id=je2.id, account_id=ar.id, debit=0, credit=Decimal('40.00')))
        
        db.session.commit()
        
        # Cash Flow for 2025
        report = get_cash_flow(date(2025, 1, 1), date(2025, 12, 31))
        
        # AR balance as of Jan 1 is 0
        # AR balance as of Dec 31 is 100 - 40 = 60
        # Change in AR is 60. Impact on cash flow is -60.
        assert report['change_in_ar'] == -60.0
        assert report['net_income'] == 100.0
        assert report['ending_cash'] == 40.0
        assert report['net_operating_cash'] == 40.0 # 100 - 60 = 40

def test_cash_flow_ap_change(app):
    with app.app_context():
        bank = Account.query.filter_by(code='1000').first()
        ap = Account.query.filter_by(code='2000').first()
        expense = Account(name='Supplies', code='5000', type='Expense', subtype='Operating Expense')
        db.session.add(expense)
        db.session.commit()
        
        # Transaction 1: Bill (Debit Expense, Credit AP) - Jan 15 2025
        je1 = JournalEntry(date=date(2025, 1, 15), memo='Bill 1')
        db.session.add(je1)
        db.session.flush()
        db.session.add(JournalEntryLine(journal_entry_id=je1.id, account_id=expense.id, debit=Decimal('50.00'), credit=0))
        db.session.add(JournalEntryLine(journal_entry_id=je1.id, account_id=ap.id, debit=0, credit=Decimal('50.00')))
        
        # Transaction 2: Payment (Debit AP, Credit Bank) - Feb 15 2025
        je2 = JournalEntry(date=date(2025, 2, 15), memo='Vendor Payment 1')
        db.session.add(je2)
        db.session.flush()
        db.session.add(JournalEntryLine(journal_entry_id=je2.id, account_id=ap.id, debit=Decimal('20.00'), credit=0))
        db.session.add(JournalEntryLine(journal_entry_id=je2.id, account_id=bank.id, debit=0, credit=Decimal('20.00')))
        
        db.session.commit()
        
        # Cash Flow for 2025
        report = get_cash_flow(date(2025, 1, 1), date(2025, 12, 31))
        
        # AP balance as of Jan 1 is 0
        # AP balance as of Dec 31 is 50 - 20 = 30
        # Change in AP is 30. Impact on cash flow is +30.
        assert report['change_in_ap'] == 30.0
        assert report['net_income'] == -50.0
        assert report['ending_cash'] == -20.0
        assert report['net_operating_cash'] == -20.0 # -50 + 30 = -20

def test_cash_flow_with_non_bank_subtype(app):
    with app.app_context():
        savings = Account.query.filter_by(code='1058').first()
        revenue = Account.query.filter_by(code='4000').first()
        
        # Transaction: Direct Cash Sale to Savings account
        je = JournalEntry(date=date(2025, 3, 1), memo='Cash Sale')
        db.session.add(je)
        db.session.flush()
        db.session.add(JournalEntryLine(journal_entry_id=je.id, account_id=savings.id, debit=Decimal('50.00'), credit=0))
        db.session.add(JournalEntryLine(journal_entry_id=je.id, account_id=revenue.id, debit=0, credit=Decimal('50.00')))
        
        db.session.commit()
        
        report = get_cash_flow(date(2025, 1, 1), date(2025, 12, 31))
        
        # Savings account (subtype 'Savings') should be counted as cash
        assert report['ending_cash'] == 50.0
        assert report['net_change_in_cash'] == 50.0

def test_cash_flow_financing(app):
    with app.app_context():
        bank = Account.query.filter_by(code='1000').first()
        loan = Account(name='Bank Loan', code='2010', type='Liability', subtype='Bank Loans')
        equity = Account(name='Owner Contribution', code='3000', type='Equity', subtype='Partner Contributions')
        db.session.add_all([loan, equity])
        db.session.commit()
        
        # Transaction 1: Owner Contribution (Debit Bank, Credit Equity)
        je1 = JournalEntry(date=date(2025, 1, 1), memo='Owner invest')
        db.session.add(je1)
        db.session.flush()
        db.session.add(JournalEntryLine(journal_entry_id=je1.id, account_id=bank.id, debit=Decimal('1000.00'), credit=0))
        db.session.add(JournalEntryLine(journal_entry_id=je1.id, account_id=equity.id, debit=0, credit=Decimal('1000.00')))
        
        # Transaction 2: Take Loan (Debit Bank, Credit Loan)
        je2 = JournalEntry(date=date(2025, 2, 1), memo='Get loan')
        db.session.add(je2)
        db.session.flush()
        db.session.add(JournalEntryLine(journal_entry_id=je2.id, account_id=bank.id, debit=Decimal('500.00'), credit=0))
        db.session.add(JournalEntryLine(journal_entry_id=je2.id, account_id=loan.id, debit=0, credit=Decimal('500.00')))
        
        db.session.commit()
        
        report = get_cash_flow(date(2025, 1, 1), date(2025, 12, 31))
        
        assert report['net_financing_cash'] == 1500.0
        assert report['net_change_in_cash'] == 1500.0
