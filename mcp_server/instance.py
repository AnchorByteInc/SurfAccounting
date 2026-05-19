from fastmcp import FastMCP
from mcp_server.middleware import ApiKeyAuthMiddleware

# Initialize the FastMCP instance with API key authentication middleware
mcp = FastMCP(
    "Surf Accounting",
    middleware=[ApiKeyAuthMiddleware()],
)
