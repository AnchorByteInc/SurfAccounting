from marshmallow import fields, validate, EXCLUDE
from ..extensions import ma, db
from ..models.customer import Customer

class CustomerSchema(ma.SQLAlchemyAutoSchema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    primary_contact_name = fields.String(allow_none=True, validate=validate.Length(max=100))
    email = fields.Email(allow_none=True)
    phone = fields.String(allow_none=True, validate=validate.Length(max=20))
    website = fields.String(allow_none=True, validate=validate.Length(max=255))
    billing_address = fields.String(allow_none=True)
    shipping_address = fields.String(allow_none=True)
    balance = fields.Decimal(dump_only=True)

    class Meta:
        model = Customer
        load_instance = True
        sqla_session = db.session
        unknown = EXCLUDE

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)
