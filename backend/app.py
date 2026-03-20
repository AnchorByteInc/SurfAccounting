import os
from flask import Flask, jsonify, request, send_from_directory
from sqlalchemy.exc import IntegrityError
from .config import Config
from .extensions import db, migrate, jwt, cors, ma
from flask_jwt_extended import verify_jwt_in_request
from flask_jwt_extended.exceptions import NoAuthorizationError, InvalidHeaderError, JWTDecodeError, WrongTokenError
import jwt as pyjwt

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Security warnings for default keys
    if not os.environ.get('SECRET_KEY') and app.config['ENV'] != 'production':
        app.logger.warning("SECRET_KEY not set, using development default. DO NOT USE IN PRODUCTION.")
    if not os.environ.get('JWT_SECRET_KEY') and app.config['ENV'] != 'production':
        app.logger.warning("JWT_SECRET_KEY not set, using development default. DO NOT USE IN PRODUCTION.")

    # Ensure upload folder exists
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])

    # Initialize extensions
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)
    cors.init_app(app)
    ma.init_app(app)

    # Global JWT protection
    @app.before_request
    def protect_routes():
        # List of public endpoints
        public_endpoints = [
            'auth.login', 
            'auth.forgot_password', 
            'auth.reset_password', 
            'health_check', 
            'static', 
            'uploaded_file'
        ]
        
        # Check if the current endpoint is public or if it's an OPTIONS request (for CORS)
        if request.endpoint in public_endpoints or request.method == 'OPTIONS':
            return
            
        try:
            verify_jwt_in_request()
        except (NoAuthorizationError, InvalidHeaderError, JWTDecodeError, WrongTokenError, pyjwt.exceptions.PyJWTError) as e:
            return jsonify({"msg": str(e)}), 401

    # Register blueprints
    from .auth import auth_bp
    from .customers import customers_bp
    from .vendors import vendors_bp
    from .invoices import invoices_bp
    from .accounts import accounts_bp
    from .bills import bills_bp
    from .bank_accounts import bank_accounts_bp
    from .settings import settings_bp
    from .journals import journals_bp
    from .payments import payments_bp
    from .dashboard import dashboard_bp
    from .reports import reports_bp
    from .accounting_periods import accounting_periods_bp
    from .taxes import taxes_bp
    from .items import items_bp

    app.register_blueprint(auth_bp, url_prefix='/api')
    app.register_blueprint(customers_bp, url_prefix='/api')
    app.register_blueprint(vendors_bp, url_prefix='/api')
    app.register_blueprint(invoices_bp, url_prefix='/api')
    app.register_blueprint(accounts_bp, url_prefix='/api')
    app.register_blueprint(bills_bp, url_prefix='/api')
    app.register_blueprint(bank_accounts_bp, url_prefix='/api')
    app.register_blueprint(settings_bp, url_prefix='/api')
    app.register_blueprint(journals_bp, url_prefix='/api')
    app.register_blueprint(payments_bp, url_prefix='/api')
    app.register_blueprint(dashboard_bp, url_prefix='/api')
    app.register_blueprint(reports_bp, url_prefix='/api')
    app.register_blueprint(accounting_periods_bp, url_prefix='/api')
    app.register_blueprint(taxes_bp, url_prefix='/api')
    app.register_blueprint(items_bp, url_prefix='/api')

    # Global Error Handlers (10.1.3)
    @app.errorhandler(ValueError)
    def handle_value_error(e):
        return jsonify({"msg": str(e), "error": "validation_error"}), 400

    @app.errorhandler(IntegrityError)
    def handle_integrity_error(e):
        # Extract the original error from SQLite if possible
        msg = str(e.orig) if hasattr(e, 'orig') else str(e)
        
        # Provide more user-friendly messages for common integrity errors
        user_msg = "Database integrity error. Please check for related records."
        
        if "NOT NULL constraint failed: invoices.customer_id" in msg:
            user_msg = "Cannot delete customer because they have associated invoices."
        elif "NOT NULL constraint failed: bills.vendor_id" in msg:
            user_msg = "Cannot delete vendor because they have associated bills."
        elif "FOREIGN KEY constraint failed" in msg:
            user_msg = "This record is being used by other records and cannot be deleted."
        elif "UNIQUE constraint failed" in msg:
            user_msg = "This record already exists (duplicate entry)."
        else:
            # Fallback to the original message if it's not a common one, 
            # but keep it as a 'msg' so the frontend can display it.
            user_msg = f"Database error: {msg}"

        return jsonify({"msg": user_msg, "message": user_msg, "error": "integrity_error"}), 409

    @app.errorhandler(404)
    def handle_404_error(e):
        return jsonify({"msg": "Resource not found", "error": "not_found"}), 404

    @app.errorhandler(Exception)
    def handle_unexpected_error(e):
        # We don't want to leak detailed info in production, but in debug we might.
        # But for this project, let's keep it consistent.
        app.logger.error(f"Unexpected error: {str(e)}")
        return jsonify({"msg": "An unexpected error occurred", "error": "server_error"}), 500

    @app.route('/health', methods=['GET'])
    def health_check():
        return jsonify({"status": "healthy", "service": "surf-backend"}), 200

    @app.route('/uploads/<path:filename>')
    def uploaded_file(filename):
        return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

    return app

def main():
    app = create_app()
    app.run(host='0.0.0.0', port=5001, debug=True)

if __name__ == '__main__':
    main()
