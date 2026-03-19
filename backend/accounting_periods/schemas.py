from ..extensions import ma
from ..models.accounting_period import AccountingPeriod

class AccountingPeriodSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = AccountingPeriod
        load_instance = True
        include_fk = True

accounting_period_schema = AccountingPeriodSchema()
accounting_period_list_schema = AccountingPeriodSchema(many=True)
