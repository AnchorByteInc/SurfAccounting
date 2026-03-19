from marshmallow import fields, validate, validates, ValidationError, validates_schema, EXCLUDE
from ..extensions import ma, db
from ..models.journal import JournalEntry, JournalEntryLine
from ..models.account import Account
from ..utils.money import to_decimal


class JournalEntryLineSchema(ma.SQLAlchemyAutoSchema):
    journal_entry_id = fields.Integer(required=False, allow_none=True)
    account_id = fields.Integer(required=True)
    debit = fields.Decimal(required=False, allow_none=True, as_string=True)
    credit = fields.Decimal(required=False, allow_none=True, as_string=True)
    description = fields.String(allow_none=True)

    class Meta:
        model = JournalEntryLine
        load_instance = True
        sqla_session = db.session
        include_fk = True
        unknown = EXCLUDE

    @validates("journal_entry_id")
    def validate_journal_entry_id(self, value, **kwargs):
        if value is None:
            return
        if not db.session.get(JournalEntry, value):
            raise ValidationError("JournalEntry does not exist")

    @validates("account_id")
    def validate_account_id(self, value, **kwargs):
        if value is None:
            return
        if not db.session.get(Account, value):
            raise ValidationError("Account does not exist")

    @validates_schema
    def validate_amounts(self, data, **kwargs):
        debit = data.get("debit")
        credit = data.get("credit")
        # Normalize None to 0 for checks; marshmallow Decimal as string -> allow only presence
        d = to_decimal(debit) if debit is not None else to_decimal(0)
        c = to_decimal(credit) if credit is not None else to_decimal(0)
        if d < 0 or c < 0:
            raise ValidationError("Amounts must be non-negative")
        if (d == 0 and c == 0) or (d > 0 and c > 0):
            raise ValidationError("Exactly one of debit or credit must be greater than zero")


class JournalEntrySchema(ma.SQLAlchemyAutoSchema):
    date = fields.Date(required=True)
    memo = fields.String(validate=validate.Length(max=255))
    reference = fields.String(validate=validate.Length(max=100))
    transaction_type = fields.String(validate=validate.Length(max=50))
    source_module = fields.String(validate=validate.Length(max=20))
    source_id = fields.Integer()
    vendor_id = fields.Integer(allow_none=True)
    customer_id = fields.Integer(allow_none=True)

    lines = fields.Nested(JournalEntryLineSchema, many=True)

    class Meta:
        model = JournalEntry
        load_instance = True
        sqla_session = db.session
        include_fk = True
        unknown = EXCLUDE


journal_entry_schema = JournalEntrySchema()
journal_entries_schema = JournalEntrySchema(many=True)
journal_entry_line_schema = JournalEntryLineSchema()
journal_entry_lines_schema = JournalEntryLineSchema(many=True)
