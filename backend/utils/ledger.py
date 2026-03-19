from decimal import Decimal
from ..extensions import db
from ..models.journal import JournalEntryLine


def get_account_balance(account_id: int) -> Decimal:
    """Compute current balance for an account from journal lines: sum(debit - credit)."""
    result = db.session.query(
        db.func.coalesce(db.func.sum(JournalEntryLine.debit - JournalEntryLine.credit), 0)
    ).filter(JournalEntryLine.account_id == account_id).scalar()
    return Decimal(str(result))
