import pytest

from bambu_forge.prepare.slicer import build_slice_command, mock_slice_result, run_slicer


def test_build_slice_command():
    cmd = build_slice_command(
        slicer_path="/app/BambuStudio",
        input_file="/models/box.stl",
        output_file="/exports/box.3mf",
        machine_settings="/profiles/machine.json",
        process_settings="/profiles/process.json",
        filament_settings="/profiles/filament.json",
        plate_index=0,
    )

    assert cmd[0] == "/app/BambuStudio"
    assert "--slice" in cmd
    assert "--export-3mf" in cmd
    assert "/exports/box.3mf" in cmd
    assert "/models/box.stl" in cmd
    assert "--load-settings" in cmd
    assert "/profiles/process.json" in cmd
    assert "--load-filaments" in cmd
    assert "/profiles/filament.json" in cmd


def test_mock_slice():
    result = mock_slice_result("/models/box.stl")

    assert result["success"] is True
    assert result["print_time"] == 128
    assert result["filament_grams"] == 22.8
    assert result["layers"] == 187


def test_slicer_not_found(tmp_path):
    result = run_slicer(
        slicer_path="/nonexistent/BambuStudio",
        input_file=str(tmp_path / "box.stl"),
        output_file=str(tmp_path / "box.3mf"),
    )

    assert result["success"] is False
    assert "not found" in result["error"].lower()
