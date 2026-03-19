from marshmallow import fields, validate, validates, ValidationError, EXCLUDE, post_load
from ..extensions import ma, db
from ..models.invoice import Invoice, InvoiceLine
from ..models.account import Account
from ..models.tax import Tax
from ..taxes.schemas import TaxSchema
from ..customers.schemas import CustomerSchema

class InvoiceLineSchema(ma.SQLAlchemyAutoSchema):
    line_total = fields.Decimal(dump_only=True)
    invoice_id = fields.Integer(required=False, allow_none=True)
    item_id = fields.Integer(required=False, allow_none=True)
    account_id = fields.Integer(required=True)
    taxes = fields.Nested(TaxSchema, many=True, dump_only=True)
    tax_ids = fields.List(fields.Integer(), load_only=True)
    
    class Meta:
        model = InvoiceLine
        load_instance = True
        sqla_session = db.session
        include_fk = True
        unknown = EXCLUDE

    @validates("invoice_id")
    def validate_invoice_id(self, value, **kwargs):
        if value is None:
            return
        if not db.session.get(Invoice, value):
            raise ValidationError("Invoice does not exist")

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

class InvoiceSchema(ma.SQLAlchemyAutoSchema):
    invoice_number = fields.String(required=False, allow_none=True, validate=validate.Length(max=50))
    status = fields.String(validate=validate.OneOf(['draft', 'approved', 'sent', 'paid', 'overdue', 'cancelled']))
    subtotal = fields.Decimal(dump_only=True)
    tax = fields.Decimal(dump_only=True)
    tax_breakdown = fields.List(fields.Dict(), dump_only=True)
    total = fields.Decimal(dump_only=True)
    balance = fields.Decimal(dump_only=True)
    
    lines = fields.Nested(InvoiceLineSchema, many=True)
    customer = fields.Nested(CustomerSchema, dump_only=True)
    
    class Meta:
        model = Invoice
        load_instance = True
        sqla_session = db.session
        include_fk = True
        unknown = EXCLUDE

invoice_schema = InvoiceSchema()
invoices_schema = InvoiceSchema(many=True)
invoice_line_schema = InvoiceLineSchema()
invoice_lines_schema = InvoiceLineSchema(many=True)
