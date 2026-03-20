import os
import sys
from contextlib import contextmanager
from flask import Flask

# Add the project root to sys.path to allow imports from backend/
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from backend.config import Config  # noqa: E402
from backend.extensions import db  # noqa: E402

def create_app(config_class=Config):
    """
    Minimal Flask application factory to initialize database and reuse models.
    """
    app = Flask(__name__)
    app.config.from_object(config_class)
    db.init_app(app)
    return app

# Initialize the app context for database access
app = create_app()

@contextmanager
def get_db_session():
    """
    Context manager to handle database sessions for each MCP tool call.
    Uses app context to ensure thread-safe session handling and atomicity.
    Rolls back on ANY exception that escapes the context.
    """
    with app.app_context():
        try:
            yield db.session
            db.session.commit()
        except Exception:
            db.session.rollback()
            raise
        finally:
            db.session.remove()
