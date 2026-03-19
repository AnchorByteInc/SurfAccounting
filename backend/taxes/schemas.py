from marshmallow import fields, validate, EXCLUDE
from ..extensions import ma, db
from ..models.tax import Tax

class TaxSchema(ma.SQLAlchemyAutoSchema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    rate = fields.Decimal(as_string=True, required=True, validate=validate.Range(min=0))
    description = fields.String(allow_none=True)
    is_active = fields.Boolean()
    asset_account_id = fields.Integer(allow_none=True)
    liability_account_id = fields.Integer(allow_none=True)

    class Meta:
        model = Tax
        load_instance = True
        sqla_session = db.session
        unknown = EXCLUDE

tax_schema = TaxSchema()
taxes_schema = TaxSchema(many=True)
