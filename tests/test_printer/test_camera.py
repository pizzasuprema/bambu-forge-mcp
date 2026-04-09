import pytest


@pytest.mark.asyncio
async def test_calibrate_mock():
    from bambu_forge.printer.tools import calibrate_impl

    result = await calibrate_impl(calibration_type="bed_leveling", mock=True)
    assert result["status"] == "success"
    assert "bed_leveling" in result["message"]
    assert "Monitor progress" in result["message"]


@pytest.mark.asyncio
async def test_calibrate_invalid_type():
    from bambu_forge.printer.tools import calibrate_impl

    result = await calibrate_impl(calibration_type="unknown_thing", mock=True)
    assert result["status"] == "error"
    assert result["error_code"] == "CALIBRATION_UNSUPPORTED"
    assert "unknown_thing" in result["message"]


@pytest.mark.asyncio
async def test_camera_mock(tmp_path):
    from bambu_forge.printer.camera import capture_snapshot

    result = await capture_snapshot(camera="liveview", mock=True, workspace=str(tmp_path))
    assert result["status"] == "success"
    assert "file_path" in result
    assert result["camera"] == "liveview"
    assert (tmp_path / "snapshot_liveview.png").exists()
