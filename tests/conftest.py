from backend.config import Config

# Set default test credentials for bootstrap if not provided
# These are used by the fallback login mechanism when no users exist in the DB.
if not Config.AUTH_USER:
    Config.AUTH_USER = "admin"
if not Config.AUTH_PASS:
    Config.AUTH_PASS = "admin123"
