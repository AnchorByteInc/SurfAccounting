import secrets
import hashlib
from datetime import datetime
from backend.extensions import db
from .base import BaseModel


class ApiKey(db.Model, BaseModel):
    __tablename__ = 'api_keys'

    name = db.Column(db.String(100), nullable=False)
    key_prefix = db.Column(db.String(8), nullable=False)
    key_hash = db.Column(db.String(64), unique=True, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    last_used_at = db.Column(db.DateTime, nullable=True)
    expires_at = db.Column(db.DateTime, nullable=True)
    created_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    creator = db.relationship('User', backref='api_keys')

    @staticmethod
    def generate_key():
        """Generate a new API key. Returns (raw_key, prefix, hash)."""
        raw_key = f"sk_{secrets.token_hex(32)}"
        prefix = raw_key[:8]
        key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
        return raw_key, prefix, key_hash

    @staticmethod
    def hash_key(raw_key):
        """Hash a raw API key for lookup."""
        return hashlib.sha256(raw_key.encode()).hexdigest()

    @property
    def is_expired(self):
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at

    @property
    def is_valid(self):
        return self.is_active and not self.is_expired

    def to_dict(self):
        data = super().to_dict()
        data['is_expired'] = self.is_expired
        if 'key_hash' in data:
            del data['key_hash']
        return data
