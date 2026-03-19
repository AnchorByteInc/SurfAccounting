import os
import logging
from dotenv import load_dotenv

# Load .env file from the project root
# Using os.path.dirname(os.path.dirname(__file__)) to get to the root from backend/config.py
basedir = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
load_dotenv(os.path.join(basedir, '.env'))

logger = logging.getLogger(__name__)

class Config:
    ENV = os.environ.get('FLASK_ENV', 'development')
    SECRET_KEY = os.environ.get('SECRET_KEY')
    if not SECRET_KEY:
        if ENV == 'production':
            raise RuntimeError("SECRET_KEY environment variable is required in production")
        logger.warning("SECRET_KEY not set, using default development key. DO NOT USE IN PRODUCTION.")
        SECRET_KEY = 'dev-key-keep-it-secret-a-bit-longer-now-32-bytes'

    # Database configuration
    # Check for Postgres environment variables first
    pg_host = os.environ.get('POSTGRES_HOST')
    pg_port = os.environ.get('POSTGRES_PORT', '5432')
    pg_db = os.environ.get('POSTGRES_DB')
    pg_user = os.environ.get('POSTGRES_USER')
    pg_pass = os.environ.get('POSTGRES_PASSWORD')
    pg_sslmode = os.environ.get('POSTGRES_SSLMODE', 'disable')
    pg_sslrootcert = os.environ.get('POSTGRES_SSLROOTCERT')

    if all([pg_host, pg_db, pg_user, pg_pass]):
        # Construct Postgres URI
        db_uri = f"postgresql://{pg_user}:{pg_pass}@{pg_host}:{pg_port}/{pg_db}"
        params = []
        if pg_sslmode:
            params.append(f"sslmode={pg_sslmode}")
        if pg_sslrootcert:
            params.append(f"sslrootcert={pg_sslrootcert}")
        
        if params:
            db_uri += "?" + "&".join(params)
        
        SQLALCHEMY_DATABASE_URI = db_uri
    else:
        SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', f"sqlite:///{os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data.sqlite')}")
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY')
    if not JWT_SECRET_KEY:
        if ENV == 'production':
            raise RuntimeError("JWT_SECRET_KEY environment variable is required in production")
        logger.warning("JWT_SECRET_KEY not set, using default development key. DO NOT USE IN PRODUCTION.")
        JWT_SECRET_KEY = 'jwt-dev-key-that-is-at-least-32-bytes-long-for-security'
    
    JWT_ACCESS_TOKEN_EXPIRES = int(os.environ.get('JWT_ACCESS_TOKEN_EXPIRES', 3600))
    
    # File Uploads
    UPLOAD_FOLDER = os.path.join(basedir, 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size

    # Admin Credentials for bootstrapping (only used if no users exist in DB)
    # These should be moved to environment variables for security.
    AUTH_USER = os.environ.get('AUTH_USER')
    AUTH_PASS = os.environ.get('AUTH_PASS')

    # Mailgun (for password reset, etc.)
    MAILGUN_URL = os.environ.get('MAILGUN_URL')
    MAILGUN_KEY = os.environ.get('MAILGUN_KEY')
    MAILGUN_SEND_FROM_ADDRESS = os.environ.get('MAILGUN_SEND_FROM_ADDRESS')
    FRONTEND_URL = os.environ.get('FRONTEND_URL', 'http://localhost:5173')
