from marshmallow import fields, validate, validates, ValidationError, EXCLUDE
from ..extensions import ma, db
from ..models.bank import BankAccount
from ..models.account import Account


class BankAccountSchema(ma.SQLAlchemyAutoSchema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    account_number = fields.String(allow_none=True, validate=validate.Length(max=50))
    account_id = fields.Integer(required=True)

    class Meta:
        model = BankAccount
        load_instance = True
        sqla_session = db.session
        include_fk = True
        unknown = EXCLUDE

    @validates("account_id")
    def validate_account_id(self, value, **kwargs):
        if value is None:
            return
        if not db.session.get(Account, value):
            raise ValidationError("Account does not exist")


bank_account_schema = BankAccountSchema()
bank_accounts_schema = BankAccountSchema(many=True)
