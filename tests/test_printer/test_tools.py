import pytest


@pytest.mark.asyncio
async def test_printer_status_mock():
    from bambu_forge.printer.tools import printer_status_impl

    result = await printer_status_impl(mock=True)
    assert result["status"] == "success"
    assert result["data"]["state"] == "IDLE"


@pytest.mark.asyncio
async def test_send_gcode_blocked():
    from bambu_forge.printer.tools import send_gcode_impl

    result = await send_gcode_impl(gcode="M502", mock=True, printer_model="H2C")
    assert result["status"] == "error"
    assert result["error_code"] == "GCODE_BLOCKED"


@pytest.mark.asyncio
async def test_send_gcode_allowed():
    from bambu_forge.printer.tools import send_gcode_impl

    result = await send_gcode_impl(gcode="G28", mock=True, printer_model="H2C")
    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_manage_printer_temp_in_range():
    from bambu_forge.printer.tools import manage_printer_impl

    result = await manage_printer_impl(
        setting="nozzle_temp", value=200, mock=True, printer_model="H2C"
    )
    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_manage_printer_temp_out_of_range():
    from bambu_forge.printer.tools import manage_printer_impl

    result = await manage_printer_impl(
        setting="nozzle_temp", value=400, mock=True, printer_model="H2C"
    )
    assert result["status"] == "error"
    assert result["error_code"] == "TEMP_OUT_OF_RANGE"


@pytest.mark.asyncio
async def test_control_print_pause():
    from bambu_forge.printer.tools import control_print_impl

    result = await control_print_impl(action="pause", value=None, mock=True)
    assert result["status"] == "success"


@pytest.mark.asyncio
async def test_manage_ams_status():
    from bambu_forge.printer.tools import manage_ams_impl

    result = await manage_ams_impl(action="status", params=None, mock=True)
    assert result["status"] == "success"
    assert "trays" in result["data"]
