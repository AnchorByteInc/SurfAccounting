from marshmallow import fields, validate, post_load, EXCLUDE
from ..extensions import ma, db
from ..models.item import Item
from ..models.tax import Tax
from ..taxes.schemas import TaxSchema

class ItemSchema(ma.SQLAlchemyAutoSchema):
    name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    price = fields.Decimal(as_string=True)
    sales_taxes = fields.Nested(TaxSchema, many=True, dump_only=True)
    sales_tax_ids = fields.List(fields.Integer(), load_only=True)

    class Meta:
        model = Item
        load_instance = True
        sqla_session = db.session
        include_fk = True
        unknown = EXCLUDE

    @post_load
    def handle_taxes(self, data, **kwargs):
        tax_ids = data.pop('sales_tax_ids', None)
        if tax_ids is not None:
            data['sales_taxes'] = Tax.query.filter(Tax.id.in_(tax_ids)).all()
        return data

item_schema = ItemSchema()
items_schema = ItemSchema(many=True)
