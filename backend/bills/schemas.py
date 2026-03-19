from marshmallow import fields, validate, validates, ValidationError, EXCLUDE, post_load
from ..extensions import ma, db
from ..models.bill import Bill, BillLine
from ..models.account import Account
from ..models.tax import Tax
from ..taxes.schemas import TaxSchema

class BillLineSchema(ma.SQLAlchemyAutoSchema):
    line_total = fields.Decimal(dump_only=True)
    bill_id = fields.Integer(required=False, allow_none=True)
    item_id = fields.Integer(required=False, allow_none=True)
    account_id = fields.Integer(required=True)
    taxes = fields.Nested(TaxSchema, many=True, dump_only=True)
    tax_ids = fields.List(fields.Integer(), load_only=True)
    
    class Meta:
        model = BillLine
        load_instance = True
        sqla_session = db.session
        include_fk = True
        unknown = EXCLUDE

    @validates("bill_id")
    def validate_bill_id(self, value, **kwargs):
        if value is None:
            return
        if not db.session.get(Bill, value):
            raise ValidationError("Bill does not exist")

    @validates("account_id")
    def validate_account_id(self, value, **kwargs):
        if value is None:
            return
        if not db.session.get(Account, value):
            raise ValidationError("Account does not exist")

    @post_load
    def handle_taxes(self, data, **kwargs):
        tax_ids = data.pop('tax_ids', None)
        if tax_ids is not None:
            data['taxes'] = Tax.query.filter(Tax.id.in_(tax_ids)).all()
        return data

class BillSchema(ma.SQLAlchemyAutoSchema):
    bill_number = fields.String(required=True, validate=validate.Length(min=1, max=50))
    status = fields.String(validate=validate.OneOf(['draft', 'approved', 'paid', 'overdue', 'cancelled']))
    subtotal = fields.Decimal(dump_only=True)
    tax = fields.Decimal(dump_only=True)
    tax_breakdown = fields.List(fields.Dict(), dump_only=True)
    total = fields.Decimal(dump_only=True)
    balance = fields.Decimal(dump_only=True)
    
    lines = fields.Nested(BillLineSchema, many=True)
    
    class Meta:
        model = Bill
        load_instance = True
        sqla_session = db.session
        include_fk = True
        unknown = EXCLUDE

bill_schema = BillSchema()
bills_schema = BillSchema(many=True)
bill_line_schema = BillLineSchema()
bill_lines_schema = BillLineSchema(many=True)
