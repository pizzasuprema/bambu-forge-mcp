import pytest


@pytest.mark.asyncio
async def test_all_tools_registered():
    from bambu_forge.server import mcp

    tools = await mcp.list_tools()
    tool_names = [t.name for t in tools]

    expected = [
        # Server
        "ping",
        "discover_printers",
        "setup_printer",
        # Printer
        "printer_status",
        "start_print",
        "control_print",
        "send_gcode",
        "manage_ams",
        "manage_printer",
        "calibrate",
        "camera_snapshot",
        # Profiles
        "list_profiles",
        "get_profile",
        "save_profile",
        "delete_profile",
        "recommend_profile",
        "list_filaments",
        "import_studio_config",
        # Model — Phase 2
        "generate_model",
        "list_designs",
        # Model — Phase 3
        "generate_model_ai",
        "check_generation",
        "modify_model",
        "combine_models",
        "generate_2d_pattern",
        "search_marketplace",
        # Prepare
        "slice_model",
        "analyze_printability",
        "optimize_settings",
        "estimate_cost",
        "arrange_plate",
        "export_project",
    ]
    for name in expected:
        assert name in tool_names, f"Missing tool: {name}"

    assert len(tool_names) == 32, f"Expected 32 tools, got {len(tool_names)}: {sorted(tool_names)}"
