import pytest
from starlette.testclient import TestClient

from mcp_server.instance import mcp
# Ensure server card routes and tools are registered
import mcp_server.server  # noqa: F401


@pytest.fixture(scope="module")
def starlette_app():
    """Create a Starlette app from the FastMCP instance for testing custom routes."""
    return mcp.http_app()


@pytest.fixture(scope="module")
def client(starlette_app):
    return TestClient(starlette_app)


def test_server_card_returns_200(client):
    response = client.get("/.well-known/mcp/server-card.json")
    assert response.status_code == 200


def test_server_card_has_required_fields(client):
    response = client.get("/.well-known/mcp/server-card.json")
    card = response.json()
    assert "$schema" in card
    assert card["$schema"] == "https://static.modelcontextprotocol.io/schemas/2025-12-11/server.schema.json"
    assert "name" in card
    assert "title" in card
    assert "description" in card
    assert "version" in card


def test_server_card_has_icons(client):
    response = client.get("/.well-known/mcp/server-card.json")
    card = response.json()
    assert "icons" in card
    assert len(card["icons"]) > 0
    icon = card["icons"][0]
    assert "src" in icon
    assert icon["src"].endswith("/logo.svg")
    assert icon["mimeType"] == "image/svg+xml"


def test_server_card_has_remotes(client):
    response = client.get("/.well-known/mcp/server-card.json")
    card = response.json()
    assert "remotes" in card
    assert len(card["remotes"]) > 0
    remote = card["remotes"][0]
    assert remote["type"] == "streamable-http"
    assert remote["url"].endswith("/mcp")


def test_server_card_has_tools(client):
    response = client.get("/.well-known/mcp/server-card.json")
    card = response.json()
    assert "tools" in card
    assert isinstance(card["tools"], list)
    # Should have at least the health/ping tools
    tool_names = [t["name"] for t in card["tools"]]
    assert len(tool_names) > 0
    for tool in card["tools"]:
        assert "name" in tool
        assert "description" in tool


def test_server_card_title_matches_mcp_name(client):
    response = client.get("/.well-known/mcp/server-card.json")
    card = response.json()
    assert card["title"] == mcp.name
