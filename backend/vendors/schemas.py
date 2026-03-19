from marshmallow import fields, validate, EXCLUDE
from ..extensions import ma, db
from ..models.vendor import Vendor

class VendorSchema(ma.SQLAlchemyAutoSchema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    primary_contact_name = fields.String(allow_none=True, validate=validate.Length(max=100))
    email = fields.Email(allow_none=True)
    phone = fields.String(allow_none=True, validate=validate.Length(max=20))
    address = fields.String(allow_none=True)
    balance = fields.Decimal(dump_only=True)

    class Meta:
        model = Vendor
        load_instance = True
        sqla_session = db.session
        unknown = EXCLUDE

vendor_schema = VendorSchema()
vendors_schema = VendorSchema(many=True)
