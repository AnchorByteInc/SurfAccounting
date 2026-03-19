from ..extensions import db
from .base import BaseModel
from datetime import date

class AccountingPeriod(db.Model, BaseModel):
    __tablename__ = 'accounting_periods'
    __table_args__ = (
        db.Index('ix_accounting_periods_closed_range', 'start_date', 'end_date', 'is_closed'),
    )
    
    name = db.Column(db.String(100), nullable=False)
    start_date = db.Column(db.Date, nullable=False)
    end_date = db.Column(db.Date, nullable=False)
    is_closed = db.Column(db.Boolean, default=False)

    @classmethod
    def is_date_locked(cls, check_date):
        if isinstance(check_date, str):
             check_date = date.fromisoformat(check_date)
        
        # A date is locked if it falls within any CLOSED accounting period
        period = cls.query.filter(
            cls.start_date <= check_date,
            cls.end_date >= check_date,
            cls.is_closed == True
        ).first()
        
        return period is not None

    def __repr__(self):
        return f'<AccountingPeriod {self.name} ({self.start_date} to {self.end_date}) Closed: {self.is_closed}>'
