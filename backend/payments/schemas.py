from marshmallow import fields, validate, validates, ValidationError, EXCLUDE
from ..extensions import ma, db
from ..models.payment import Payment, VendorPayment
from ..models.customer import Customer
from ..models.vendor import Vendor
from ..models.invoice import Invoice
from ..models.bill import Bill
from ..models.account import Account


class PaymentSchema(ma.SQLAlchemyAutoSchema):
    date = fields.Date(required=True)
    amount = fields.Decimal(required=True, as_string=True)
    method = fields.String(validate=validate.Length(max=50))
    customer_id = fields.Integer(required=True)
    invoice_id = fields.Integer(allow_none=True)
    account_id = fields.Integer(allow_none=True)

    class Meta:
        model = Payment
        load_instance = True
        sqla_session = db.session
        include_fk = True
        unknown = EXCLUDE

    @validates("amount")
    def validate_amount(self, value, **kwargs):
        try:
            if value is None:
                raise ValidationError("Amount is required")
            # Ensure positive amount
            if value <= 0:
                raise ValidationError("Amount must be greater than 0")
        except TypeError:
            raise ValidationError("Invalid amount")

    @validates("customer_id")
    def validate_customer_id(self, value, **kwargs):
        if not db.session.get(Customer, value):
            raise ValidationError("Customer does not exist")

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


class VendorPaymentSchema(ma.SQLAlchemyAutoSchema):
    date = fields.Date(required=True)
    amount = fields.Decimal(required=True, as_string=True)
    method = fields.String(validate=validate.Length(max=50))
    vendor_id = fields.Integer(required=True)
    bill_id = fields.Integer(allow_none=True)
    account_id = fields.Integer(allow_none=True)

    class Meta:
        model = VendorPayment
        load_instance = True
        sqla_session = db.session
        include_fk = True
        unknown = EXCLUDE

    @validates("amount")
    def validate_amount(self, value, **kwargs):
        try:
            if value is None:
                raise ValidationError("Amount is required")
            if value <= 0:
                raise ValidationError("Amount must be greater than 0")
        except TypeError:
            raise ValidationError("Invalid amount")

    @validates("vendor_id")
    def validate_vendor_id(self, value, **kwargs):
        if not db.session.get(Vendor, value):
            raise ValidationError("Vendor does not exist")

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


payment_schema = PaymentSchema()
payments_schema = PaymentSchema(many=True)
vendor_payment_schema = VendorPaymentSchema()
vendor_payments_schema = VendorPaymentSchema(many=True)
