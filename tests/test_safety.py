"""Tests for G-code and temperature safety validation."""

import pytest

from bambu_forge.printer_registry import PrinterModel


@pytest.fixture
def h2c_model():
    return PrinterModel(
        model_id="H2C",
        display_name="Bambu Lab H2C",
        nozzle_temp_max=350,
        bed_temp_max=120,
        chamber_temp_max=65,
        enclosed=True,
        modes=["fdm", "laser", "cut"],
        ams_type=None,
        build_volume=[325, 320, 320],
        dual_nozzle=True,
    )


@pytest.fixture
def a1_open_model():
    return PrinterModel(
        model_id="A1",
        display_name="Bambu Lab A1",
        nozzle_temp_max=300,
        bed_temp_max=100,
        chamber_temp_max=None,
        enclosed=False,
        modes=["fdm"],
        ams_type=None,
        build_volume=[256, 256, 256],
        dual_nozzle=False,
    )


def test_gcode_blocks_firmware_reset(h2c_model):
    from bambu_forge.safety import validate_gcode

    result = validate_gcode("M502", h2c_model)
    assert result.blocked is True
    assert "firmware reset" in result.reason.lower()


def test_gcode_blocks_eeprom_wipe_without_read(h2c_model):
    from bambu_forge.safety import validate_gcode

    result = validate_gcode("M500", h2c_model)
    assert result.blocked is True
    assert "eeprom" in result.reason.lower() or "m501" in result.reason.lower()


def test_gcode_allows_normal_commands(h2c_model):
    from bambu_forge.safety import validate_gcode

    for line in ("G28", "G1 X100 Y100 F3000", "M104 S200"):
        result = validate_gcode(line, h2c_model)
        assert result.blocked is False, line


def test_temp_validation_in_range(h2c_model):
    from bambu_forge.safety import validate_temperature

    assert validate_temperature("nozzle", 200, h2c_model).safe is True
    assert validate_temperature("bed", 60, h2c_model).safe is True
    assert validate_temperature("chamber", 50, h2c_model).safe is True


def test_temp_validation_exceeds_max(h2c_model):
    from bambu_forge.safety import validate_temperature

    assert validate_temperature("nozzle", 400, h2c_model).safe is False
    assert validate_temperature("bed", 150, h2c_model).safe is False
    assert validate_temperature("chamber", 80, h2c_model).safe is False


def test_temp_validation_chamber_on_open_printer(a1_open_model):
    from bambu_forge.safety import validate_temperature

    result = validate_temperature("chamber", 40, a1_open_model)
    assert result.safe is False
    assert "no chamber" in result.reason.lower()


def test_gcode_blocklist_matches_after_strip_and_case_normalize(h2c_model):
    from bambu_forge.safety import validate_gcode

    result = validate_gcode("  m502  ", h2c_model)
    assert result.blocked is True
    assert "firmware reset" in result.reason.lower()
