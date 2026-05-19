import os
import sys
import importlib.metadata

# Add the project root to sys.path to allow imports from backend/ and mcp/
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from starlette.requests import Request  # noqa: E402
from starlette.responses import JSONResponse, FileResponse  # noqa: E402
from mcp_server.instance import mcp  # noqa: E402
# Import tools to register them
import mcp_server.tools.health  # noqa: E402, F401
import mcp_server.tools.accounting  # noqa: E402, F401
import mcp_server.tools.bills  # noqa: E402, F401
import mcp_server.tools.customers  # noqa: E402, F401
import mcp_server.tools.invoices  # noqa: E402, F401
import mcp_server.tools.items  # noqa: E402, F401
import mcp_server.tools.payments  # noqa: E402, F401
import mcp_server.tools.vendors  # noqa: E402, F401

# Path to the logo asset
LOGO_PATH = os.path.join(
    os.path.dirname(__file__), '..', 'frontend', 'src', 'assets', 'logo.svg'
)


@mcp.custom_route("/assets/logo.svg", methods=["GET"])
async def get_logo(request: Request) -> FileResponse:
    return FileResponse(LOGO_PATH, media_type="image/svg+xml")


@mcp.custom_route("/.well-known/mcp/server-card.json", methods=["GET"])
async def server_card(request: Request) -> JSONResponse:
    # Auto-generate details from the MCP instance and project metadata
    try:
        meta = importlib.metadata.metadata("surfaccounting-mcp-server")
        name = meta["Name"] or "surfaccounting-mcp-server"
        version = meta["Version"] or "0.1.0"
        description = meta["Summary"] or ""
    except importlib.metadata.PackageNotFoundError:
        name = "surfaccounting-mcp-server"
        version = "0.1.0"
        description = "Model Context Protocol (MCP) server for Surf"

    # Collect tools from the MCP server
    mcp_tools = await mcp.list_tools()
    tools_list = []
    for tool in mcp_tools:
        tool_entry = {
            "name": tool.name,
            "description": tool.description or "",
        }
        if tool.parameters:
            tool_entry["inputSchema"] = tool.parameters
        tools_list.append(tool_entry)

    base_url = f"{request.url.scheme}://{request.url.netloc}"

    card = {
        "$schema": "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json",
        "name": name,
        "title": mcp.name,
        "description": description,
        "version": version,
        "icons": [
            {
                "src": f"{base_url}/assets/logo.svg",
                "mimeType": "image/svg+xml",
            }
        ],
        "remotes": [
            {
                "type": "streamable-http",
                "url": f"{base_url}/mcp",
                "headers": [
                    {
                        "name": "X-API-Key",
                        "description": "Surf Accounting API Key",
                        "isRequired": True,
                        "isSecret": True
                    },
                ]
            }
        ],
        "tools": tools_list,
    }

    return JSONResponse(card)


if __name__ == "__main__":
    # Configure transport and port settings (HTTP transport on port 8000)
    # The default transport is stdio, but HTTP is requested in section 1.3.3
    mcp.run(transport="http", host="0.0.0.0", port=8000)
