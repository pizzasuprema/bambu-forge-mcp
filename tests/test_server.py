import asyncio

import bambu_forge.server as srv


def setup_function():
    srv._config = None
    srv._registry = None


def test_ping_tool():
    async def _names():
        tools = await srv.mcp.list_tools()
        return [t.name for t in tools]

    assert "ping" in asyncio.run(_names())


def test_server_has_config():
    cfg = srv.get_config()
    assert cfg.mock_mode is True
