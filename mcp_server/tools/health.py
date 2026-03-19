from mcp_server.instance import mcp
from mcp_server.utils.db import get_db_session
from sqlalchemy import text

# --- Section 1.3.2: Core Server Initialization Tools ---

@mcp.tool()
def health_check() -> str:
    """
    Verify server-to-database connectivity.
    """
    try:
        with get_db_session() as session:
            # Simple query to check connectivity
            session.execute(text("SELECT 1")).scalar()
            return "Health check passed: Server and database are connected."
    except Exception as e:
        return f"Health check failed: Unable to connect to the database. Error: {str(e)}"

@mcp.tool()
def ping() -> str:
    """
    Simple ping to verify the MCP server is responding.
    """
    return "pong"
