from marshmallow import fields, validate, EXCLUDE
from ..extensions import ma, db
from ..models.settings import Settings
from ..models.user import User

class UserSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = User
        load_instance = True
        sqla_session = db.session
        unknown = EXCLUDE
        exclude = ('password_hash', 'reset_token', 'reset_token_expiry')

user_schema = UserSchema()
user_list_schema = UserSchema(many=True)

class SettingsSchema(ma.SQLAlchemyAutoSchema):
    business_name = fields.String(required=True, validate=validate.Length(min=1, max=100))
    address = fields.String(allow_none=True)
    city = fields.String(allow_none=True, validate=validate.Length(max=100))
    state = fields.String(allow_none=True, validate=validate.Length(max=100))
    zip = fields.String(allow_none=True, validate=validate.Length(max=20))
    email = fields.Email(allow_none=True, validate=validate.Length(max=100))
    default_currency = fields.String(validate=validate.Length(equal=3))
    app_logo_url = fields.String(allow_none=True, validate=validate.Length(max=255))
    invoice_logo_url = fields.String(allow_none=True, validate=validate.Length(max=255))

    class Meta:
        model = Settings
        load_instance = True
        sqla_session = db.session
        unknown = EXCLUDE

settings_schema = SettingsSchema()
settings_list_schema = SettingsSchema(many=True)
