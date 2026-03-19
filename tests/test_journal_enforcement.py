import pytest
from datetime import date
from decimal import Decimal
from backend.app import create_app
from backend.config import Config
from backend.extensions import db
from backend.models.account import Account
from backend.models.journal import JournalEntry, JournalEntryLine
from backend.services.journal_service import validate_journal_entry, save_journal_entry

class TestConfig(Config):
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    TESTING = True

@pytest.fixture
def app():
    app = create_app(TestConfig)
    
    with app.app_context():
        db.create_all()
        # Create some test accounts
        a1 = Account(name="Cash", code="1000", type="Asset")
        a2 = Account(name="Revenue", code="4000", type="Revenue")
        db.session.add_all([a1, a2])
        db.session.commit()
        yield app
        db.session.rollback()
        db.drop_all()
        db.session.remove()

def test_is_balanced_method(app):
    with app.app_context():
        a1 = Account.query.filter_by(code="1000").first()
        a2 = Account.query.filter_by(code="4000").first()
        
        entry = JournalEntry(date=date.today(), memo="Balanced Entry")
        entry.lines.append(JournalEntryLine(account_id=a1.id, debit=Decimal('100.00'), credit=Decimal('0.00')))
        entry.lines.append(JournalEntryLine(account_id=a2.id, debit=Decimal('0.00'), credit=Decimal('100.00')))
        
        assert entry.is_balanced() is True
        
        unbalanced_entry = JournalEntry(date=date.today(), memo="Unbalanced Entry")
        unbalanced_entry.lines.append(JournalEntryLine(account_id=a1.id, debit=Decimal('100.00'), credit=Decimal('0.00')))
        unbalanced_entry.lines.append(JournalEntryLine(account_id=a2.id, debit=Decimal('0.00'), credit=Decimal('50.00')))
        
        assert unbalanced_entry.is_balanced() is False

def test_validate_journal_entry_service(app):
    with app.app_context():
        a1 = Account.query.filter_by(code="1000").first()
        a2 = Account.query.filter_by(code="4000").first()
        
        entry = JournalEntry(date=date.today())
        entry.lines.append(JournalEntryLine(account_id=a1.id, debit=Decimal('100.00')))
        entry.lines.append(JournalEntryLine(account_id=a2.id, credit=Decimal('100.00')))
        
        assert validate_journal_entry(entry) is True
        
        entry.lines[1].credit = Decimal('50.00')
        with pytest.raises(ValueError, match="Journal entry is not balanced"):
            validate_journal_entry(entry)

def test_save_journal_entry_service(app):
    with app.app_context():
        a1 = Account.query.filter_by(code="1000").first()
        a2 = Account.query.filter_by(code="4000").first()
        
        entry = JournalEntry(date=date.today())
        entry.lines.append(JournalEntryLine(account_id=a1.id, debit=Decimal('100.00')))
        entry.lines.append(JournalEntryLine(account_id=a2.id, credit=Decimal('100.00')))
        
        saved_entry = save_journal_entry(entry)
        assert saved_entry.id is not None
        
        # Test saving unbalanced entry via service
        entry2 = JournalEntry(date=date.today())
        entry2.lines.append(JournalEntryLine(account_id=a1.id, debit=Decimal('100.00')))
        entry2.lines.append(JournalEntryLine(account_id=a2.id, credit=Decimal('50.00')))
        
        with pytest.raises(ValueError, match="Journal entry is not balanced"):
            save_journal_entry(entry2)

def test_db_level_enforcement(app):
    """Test that the SQLAlchemy event listener prevents saving unbalanced entries even if bypassing service."""
    with app.app_context():
        a1 = Account.query.filter_by(code="1000").first()
        a2 = Account.query.filter_by(code="4000").first()
        
        entry = JournalEntry(date=date.today())
        entry.lines.append(JournalEntryLine(account_id=a1.id, debit=Decimal('100.00')))
        entry.lines.append(JournalEntryLine(account_id=a2.id, credit=Decimal('50.00')))
        
        db.session.add(entry)
        with pytest.raises(ValueError, match="Journal entry is not balanced"):
            db.session.commit()
