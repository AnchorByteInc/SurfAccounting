from marshmallow import fields, validate, validates, ValidationError, EXCLUDE
from ..extensions import ma, db
from ..models.account import Account

ALLOWED_ACCOUNT_TYPES = [
    "Asset",
    "Liability",
    "Equity",
    "Revenue",
    "Expense",
]


class AccountSchema(ma.SQLAlchemyAutoSchema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    code = fields.String(required=True, validate=validate.Length(min=1, max=20))
    type = fields.String(required=True, validate=validate.OneOf(ALLOWED_ACCOUNT_TYPES))
    subtype = fields.String(allow_none=True, validate=validate.Length(max=50))
    parent_id = fields.Integer(allow_none=True)
    is_active = fields.Boolean(load_default=True)
    is_system = fields.Boolean(load_default=False)

    class Meta:
        model = Account
        load_instance = True
        sqla_session = db.session
        unknown = EXCLUDE

    @validates("parent_id")
    def validate_parent(self, value, **kwargs):
        if value is None:
            return
        if value == getattr(self.instance, "id", None):
            raise ValidationError("parent_id cannot be the same as the account id")
        if not Account.query.get(value):
            raise ValidationError("parent_id does not reference an existing account")


account_schema = AccountSchema()
accounts_schema = AccountSchema(many=True)
