import pytest


@pytest.mark.asyncio
async def test_all_phase1b_tools_registered():
    from bambu_forge.server import mcp

    tools = await mcp.list_tools()
    tool_names = [t.name for t in tools]

    expected = [
        "ping",
        "printer_status",
        "start_print",
        "control_print",
        "send_gcode",
        "manage_ams",
        "manage_printer",
        "calibrate",
        "camera_snapshot",
        "list_profiles",
        "get_profile",
        "save_profile",
        "delete_profile",
        "recommend_profile",
        "list_filaments",
        "import_studio_config",
        "generate_model",
        "list_designs",
        "slice_model",
        "discover_printers",
        "setup_printer",
    ]
    for name in expected:
        assert name in tool_names, f"Missing tool: {name}"

    assert len(tool_names) >= len(expected)
