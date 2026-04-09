"""Tests for printer registry: fallback data and Bambu Studio config overlay."""

import json
from pathlib import Path


def test_load_from_fallback():
    from bambu_forge.printer_registry import PrinterRegistry

    reg = PrinterRegistry(bambu_studio_path=None)
    h2c = reg.get("H2C")
    assert h2c is not None
    assert h2c.display_name == "Bambu Lab H2C"
    assert h2c.nozzle_temp_max == 350
    assert h2c.bed_temp_max == 120
    assert h2c.enclosed is True
    assert "fdm" in h2c.modes


def test_load_from_bambu_studio_dir(tmp_path):
    from bambu_forge.printer_registry import PrinterRegistry

    printers_dir = tmp_path / "printers"
    printers_dir.mkdir()
    spec = {
        "2.0.0": {
            "display_name": "Studio Test Printer",
            "model_id": "TEST1",
            "printer_is_enclosed": False,
            "printer_modes": ["fdm"],
            "print": {
                "nozzle_temp_range": [0, 275],
                "bed_temp_range": [0, 90],
            },
        }
    }
    (printers_dir / "TEST1.json").write_text(json.dumps(spec), encoding="utf-8")

    reg = PrinterRegistry(bambu_studio_path=tmp_path)
    m = reg.get("TEST1")
    assert m is not None
    assert m.display_name == "Studio Test Printer"
    assert m.nozzle_temp_max == 275
    assert m.enclosed is False


def test_bambu_studio_overrides_fallback(tmp_path):
    from bambu_forge.printer_registry import PrinterRegistry

    printers_dir = tmp_path / "printers"
    printers_dir.mkdir()
    spec = {
        "2.0.0": {
            "display_name": "H2C From Studio Override",
            "model_id": "O1C2",
            "printer_is_enclosed": False,
            "printer_modes": ["fdm", "laser"],
            "print": {
                "nozzle_temp_range": [0, 999],
                "bed_temp_range": [0, 200],
            },
        }
    }
    (printers_dir / "O1C2.json").write_text(json.dumps(spec), encoding="utf-8")

    reg = PrinterRegistry(bambu_studio_path=tmp_path)
    h2c = reg.get("H2C")
    assert h2c is not None
    assert h2c.display_name == "H2C From Studio Override"
    assert h2c.nozzle_temp_max == 999
    assert h2c.enclosed is False


def test_list_models():
    from bambu_forge.printer_registry import PrinterRegistry

    reg = PrinterRegistry(bambu_studio_path=None)
    models = reg.list_models()
    assert models == sorted(models)
    assert "H2C" in models
    assert "A1" in models
    assert "P1S" in models
    assert len(models) >= 10


def test_unknown_model():
    from bambu_forge.printer_registry import PrinterRegistry

    reg = PrinterRegistry(bambu_studio_path=None)
    assert reg.get("NONEXISTENT") is None
