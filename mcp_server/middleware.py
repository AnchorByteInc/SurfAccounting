from datetime import datetime
from fastmcp.server.middleware import Middleware
from fastmcp.server.dependencies import get_http_request
from mcp.types import TextContent

from mcp_server.utils.db import app as flask_app
from backend.extensions import db
from backend.models.api_key import ApiKey


class ApiKeyAuthMiddleware(Middleware):
    """Middleware that validates API key on every MCP tool call."""

    async def on_call_tool(self, context, call_next):
        try:
            http_request = get_http_request()
            api_key_header = http_request.headers.get("x-api-key")
        except RuntimeError:
            api_key_header = None

        if not api_key_header:
            return [TextContent(type="text", text="Error: Missing X-API-Key header. Provide a valid API key.")]

        with flask_app.app_context():
            key_hash = ApiKey.hash_key(api_key_header)
            api_key = ApiKey.query.filter_by(key_hash=key_hash).first()

            if not api_key or not api_key.is_valid:
                return [TextContent(type="text", text="Error: Invalid or expired API key.")]

            api_key.last_used_at = datetime.utcnow()
            db.session.commit()

        return await call_next(context)
