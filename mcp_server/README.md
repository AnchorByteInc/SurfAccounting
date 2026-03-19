# Surf Accounting MCP Server

This directory contains the Model Context Protocol (MCP) server for Surf Accounting. The MCP server allows AI agents (like Claude Desktop) to interact with your accounting data securely using a standardized protocol.

## Features

The MCP server exposes several tools that allow an AI to:
- **Accounting**: View the Chart of Accounts and account details.
- **Customers & Vendors**: List, search, and retrieve details for business contacts.
- **Invoices & Bills**: Query financial documents and their status.
- **Payments**: Check payment history and associations.
- **Health**: Monitor the status of the MCP server and its connection to the database.

## Setup

### Prerequisites
- Python 3.13 or higher
- The main Surf Accounting project must be set up (at least the database `data.sqlite` should exist in the root).

### Installation
The MCP server dependencies are included in the main project's `pyproject.toml` and `mcp_server/pyproject.toml`. If you've already run `uv sync` or `pip install -e .` in the root, you're ready to go.

## Running the Server

### HTTP Transport (Default)
By default, this server is configured to run over HTTP on port 8000. This is useful for remote connections or specific integrations.

```bash
python3 -m mcp_server.server
```

### STDIO Transport
If you wish to use the server with tools that expect STDIO transport (like Claude Desktop), you can modify `mcp_server/server.py` or run a script that uses the `mcp` instance with the default transport.

## Connecting to Claude Desktop

To use this server with Claude Desktop, add the following to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "surf-accounting": {
      "command": "python3",
      "args": ["-m", "mcp_server.server"],
      "env": {
        "DATABASE_URL": "sqlite:////path/to/your/SurfAccounting/data.sqlite"
      }
    }
  }
}
```
*Note: Ensure you provide the absolute path to your `data.sqlite` file.*

## Project Structure
- `server.py`: The entry point for the MCP server.
- `instance.py`: Initializes the FastMCP instance.
- `tools/`: Contains the implementation of various MCP tools.
- `utils/`: Utility functions for database access and vector storage.
- `schemas.py`: Data models and schemas.
