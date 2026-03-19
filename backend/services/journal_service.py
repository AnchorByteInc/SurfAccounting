from ..extensions import db
from ..models.journal import JournalEntry
from ..utils.validation import validate_date_is_open, validate_non_negative_amount

def validate_journal_entry(journal_entry: JournalEntry) -> bool:
    """
    3.1.1 Implement function to validate debit == credit
    Ensures that the total debits of a journal entry equal the total credits.
    Also validates that the date is not in a closed period (10.1.6) 
    and line-level non-negative amounts (10.1.1).
    """
    validate_date_is_open(journal_entry.date)
    
    if not journal_entry.lines:
        raise ValueError("Journal entry must have at least one line.")

    for line in journal_entry.lines:
        validate_non_negative_amount(line.debit or 0, "Debit")
        validate_non_negative_amount(line.credit or 0, "Credit")
        
        if (line.debit or 0) > 0 and (line.credit or 0) > 0:
            raise ValueError("A single journal entry line cannot have both debit and credit.")
        if (line.debit or 0) == 0 and (line.credit or 0) == 0:
            raise ValueError("A journal entry line must have either a debit or a credit.")

    if not journal_entry.is_balanced():
        debits = sum((line.debit or 0) for line in journal_entry.lines)
        credits = sum((line.credit or 0) for line in journal_entry.lines)
        raise ValueError(f"Journal entry is not balanced. Total Debits: {debits}, Total Credits: {credits}")
    return True

def save_journal_entry(journal_entry: JournalEntry) -> JournalEntry:
    """
    3.1.2 Prevent journal entry save if unbalanced
    Validates and saves a journal entry to the database.
    Does NOT commit; caller must commit. Flushes to generate ID.
    """
    validate_journal_entry(journal_entry)
    db.session.add(journal_entry)
    db.session.flush()
    return journal_entry
