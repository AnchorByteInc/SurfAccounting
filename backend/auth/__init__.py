from flask import Blueprint, jsonify, request, current_app
from flask_jwt_extended import create_access_token
from ..models.user import User
from ..extensions import db
from ..utils import send_email
import secrets
from datetime import datetime, timedelta

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/auth/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    user = User.query.filter_by(username=username).first()
    if user and user.check_password(password):
        if not user.is_active:
            return jsonify({"msg": "User account is disabled"}), 401
        access_token = create_access_token(identity=username)
        return jsonify(access_token=access_token, user=user.to_dict()), 200
    
    # Fallback to credentials for bootstrap if no users exist
    if User.query.count() == 0:
        auth_user = current_app.config.get('AUTH_USER')
        auth_pass = current_app.config.get('AUTH_PASS')
        if auth_user and auth_pass and username == auth_user and password == auth_pass:
            access_token = create_access_token(identity=username)
            return jsonify(access_token=access_token, user={"username": username, "is_admin": True}), 200
    
    return jsonify({"msg": "Bad username or password"}), 401

@auth_bp.route('/auth/forgot-password', methods=['POST'])
def forgot_password():
    data = request.get_json()
    email = data.get('email')
    user = User.query.filter_by(email=email).first()
    
    if user:
        # Generate a reset token
        token = secrets.token_urlsafe(32)
        user.reset_token = token
        user.reset_token_expiry = datetime.now() + timedelta(hours=1)
        db.session.commit()
        
        # Send password reset email
        reset_link = f"{current_app.config['FRONTEND_URL']}/login?token={token}"
        subject = "Password Reset Link"
        text = f"Hello,\n\nYou requested a password reset for your Surf Accounting account. Please use the link below to reset your password:\n\n{reset_link}\n\nIf you did not request a password reset, please ignore this email."
        send_email(user.email, subject, text)
        
        # For now, just return a success message.
        return jsonify({"msg": "If your email is in our system, you will receive a reset link."}), 200
    
    return jsonify({"msg": "If your email is in our system, you will receive a reset link."}), 200

@auth_bp.route('/auth/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json()
    token = data.get('token')
    new_password = data.get('password')
    
    user = User.query.filter(User.reset_token == token, User.reset_token_expiry > datetime.now()).first()
    if user:
        user.set_password(new_password)
        user.reset_token = None
        user.reset_token_expiry = None
        db.session.commit()
        return jsonify({"msg": "Password has been reset successfully"}), 200
    
    return jsonify({"msg": "Invalid or expired token"}), 400

@auth_bp.route('/auth/status', methods=['GET'])
def status():
    return jsonify({"status": "auth blueprint active"}), 200
