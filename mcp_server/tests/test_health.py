from mcp_server.tools.health import health_check, ping

def test_ping():
    assert ping() == "pong"

def test_health_check():
    assert "Health check passed" in health_check()
