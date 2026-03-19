import os
import sys

# Add the project root to sys.path to allow imports from backend/ and mcp/
root_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from mcp_server.instance import mcp
# Import tools to register them
from mcp_server.tools import accounting, customers, vendors, items, invoices, bills, payments, health

if __name__ == "__main__":
    # Configure transport and port settings (HTTP transport on port 8000)
    # The default transport is stdio, but HTTP is requested in section 1.3.3
    mcp.run(transport="http", host="0.0.0.0", port=8000)
