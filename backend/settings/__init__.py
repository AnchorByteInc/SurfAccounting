import os
from flask import Blueprint, jsonify, request, current_app
from marshmallow import ValidationError
from werkzeug.utils import secure_filename
from ..extensions import db
from ..models.settings import Settings
from ..models.user import User
from .schemas import settings_schema, settings_list_schema, user_schema, user_list_schema

settings_bp = Blueprint('settings', __name__)

@settings_bp.route('/users', methods=['GET'])
def get_users():
    users = User.query.all()
    return jsonify(user_list_schema.dump(users)), 200

@settings_bp.route('/users', methods=['POST'])
def create_user():
    data = request.get_json()
    if not data:
        return jsonify({"message": "No input data provided"}), 400
    
    password = data.pop('password', None)
    if not password:
        return jsonify({"message": "Password is required"}), 400
        
    try:
        new_user = user_schema.load(data)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        return user_schema.jsonify(new_user), 201
    except ValidationError as err:
        return jsonify(err.messages), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({"message": str(e)}), 400

@settings_bp.route('/users/<int:id>', methods=['DELETE'])
def delete_user(id):
    user = User.query.get_or_404(id)
    # Don't allow deleting the last admin or yourself? 
    # For now, just allow deleting.
    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": "User deleted"}), 200

@settings_bp.route('/settings', methods=['POST'])
def create_settings():
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No input data provided"}), 400
    
    try:
        new_settings = settings_schema.load(json_data)
        db.session.add(new_settings)
        db.session.commit()
        return settings_schema.jsonify(new_settings), 201
    except ValidationError as err:
        return jsonify(err.messages), 400

@settings_bp.route('/settings', methods=['GET'])
def get_all_settings():
    # Filtering
    business_name_filter = request.args.get('business_name')
    currency_filter = request.args.get('default_currency')
    
    query = Settings.query
    if business_name_filter:
        query = query.filter(Settings.business_name.ilike(f'%{business_name_filter}%'))
    if currency_filter:
        query = query.filter(Settings.default_currency.ilike(f'%{currency_filter}%'))
        
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)
    
    if per_page <= 0:
        settings_items = query.all()
        return jsonify({
            "settings": settings_list_schema.dump(settings_items),
            "total": len(settings_items),
            "pages": 1,
            "current_page": 1,
            "per_page": len(settings_items)
        }), 200

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    settings_items = pagination.items
    
    return jsonify({
        "settings": settings_list_schema.dump(settings_items),
        "total": pagination.total,
        "pages": pagination.pages,
        "current_page": pagination.page,
        "per_page": pagination.per_page
    }), 200

@settings_bp.route('/settings/<int:id>', methods=['GET'])
def get_settings(id):
    settings = Settings.query.get_or_404(id)
    return settings_schema.jsonify(settings), 200

@settings_bp.route('/settings/<int:id>', methods=['PUT'])
def update_settings(id):
    settings = Settings.query.get_or_404(id)
    json_data = request.get_json()
    if not json_data:
        return jsonify({"message": "No input data provided"}), 400
    
    try:
        updated_settings = settings_schema.load(json_data, instance=settings, partial=True)
        db.session.commit()
        return settings_schema.jsonify(updated_settings), 200
    except ValidationError as err:
        return jsonify(err.messages), 400

@settings_bp.route('/settings/<int:id>', methods=['DELETE'])
def delete_settings(id):
    settings = Settings.query.get_or_404(id)
    db.session.delete(settings)
    db.session.commit()
    return jsonify({"message": "Settings deleted"}), 200

@settings_bp.route('/settings/status', methods=['GET'])
def status():
    return jsonify({"status": "settings blueprint active"}), 200

def allowed_file(filename):
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'svg'}
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@settings_bp.route('/settings/upload-logo', methods=['POST'])
def upload_logo():
    if 'file' not in request.files:
        return jsonify({"message": "No file part"}), 400
    file = request.files['file']
    if file.filename == '':
        return jsonify({"message": "No selected file"}), 400
    if file and allowed_file(file.filename):
        filename = secure_filename(file.filename)
        # Add a unique prefix or hash if needed, but for now simple
        # To avoid overwriting, let's add some randomness or timestamp
        from datetime import datetime
        filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
        
        upload_path = os.path.join(current_app.config['UPLOAD_FOLDER'], 'logos')
        if not os.path.exists(upload_path):
            os.makedirs(upload_path)
            
        file.save(os.path.join(upload_path, filename))
        url = f"/uploads/logos/{filename}"
        return jsonify({"url": url}), 201
    
    return jsonify({"message": "File type not allowed"}), 400
