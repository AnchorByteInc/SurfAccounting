from datetime import datetime
from flask import Blueprint, jsonify, request
from flask_jwt_extended import get_jwt_identity
from ..extensions import db
from ..models.api_key import ApiKey
from ..models.user import User

api_keys_bp = Blueprint('api_keys', __name__)


@api_keys_bp.route('/api-keys', methods=['GET'])
def list_api_keys():
    keys = ApiKey.query.order_by(ApiKey.created_at.desc()).all()
    return jsonify([k.to_dict() for k in keys]), 200


@api_keys_bp.route('/api-keys', methods=['POST'])
def create_api_key():
    data = request.get_json()
    if not data or not data.get('name'):
        return jsonify({"message": "Name is required"}), 400

    current_username = get_jwt_identity()
    current_user = User.query.filter_by(username=current_username).first()

    # Handle bootstrap scenario: JWT is valid but no User row exists yet
    if not current_user:
        if User.query.count() == 0:
            current_user = User(
                username=current_username,
                email=f"{current_username}@localhost",
                is_admin=True,
                is_active=True,
            )
            current_user.set_password("")  # placeholder; bootstrap user
            db.session.add(current_user)
            db.session.flush()
        else:
            return jsonify({"message": "User not found"}), 401

    expires_at = None
    if data.get('expires_at'):
        try:
            expires_at = datetime.fromisoformat(data['expires_at'])
        except (ValueError, TypeError):
            return jsonify({"message": "Invalid expires_at format. Use ISO format."}), 400

    raw_key, prefix, key_hash = ApiKey.generate_key()

    api_key = ApiKey(
        name=data['name'],
        key_prefix=prefix,
        key_hash=key_hash,
        created_by=current_user.id,
        expires_at=expires_at,
    )
    db.session.add(api_key)
    db.session.commit()

    result = api_key.to_dict()
    # Return the raw key only on creation — it cannot be retrieved later
    result['key'] = raw_key

    return jsonify(result), 201


@api_keys_bp.route('/api-keys/<int:id>', methods=['DELETE'])
def revoke_api_key(id):
    api_key = ApiKey.query.get_or_404(id)
    api_key.is_active = False
    db.session.commit()
    return jsonify({"message": "API key revoked"}), 200
