from ..models.accounting_period import AccountingPeriod

def validate_date_is_open(check_date):
    """10.1.6 Lock closed accounting periods"""
    if AccountingPeriod.is_date_locked(check_date):
        raise ValueError(f"Transaction date {check_date} falls within a closed accounting period.")

def validate_positive_amount(amount, field_name="Amount"):
    """10.1.1 Fix validation edge cases"""
    if amount is None or amount <= 0:
        raise ValueError(f"{field_name} must be greater than zero.")

def validate_non_negative_amount(amount, field_name="Amount"):
    """10.1.1 Fix validation edge cases"""
    if amount is None or amount < 0:
        raise ValueError(f"{field_name} cannot be negative.")

def validate_date_order(start_date, end_date, start_field="Issue date", end_field="Due date"):
    """10.1.1 Fix validation edge cases"""
    if start_date and end_date and start_date > end_date:
        raise ValueError(f"{end_field} cannot be before {start_field}.")
