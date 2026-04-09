import json
import os
from pathlib import Path
import pytest


def test_env_vars_override_config_file(tmp_path, monkeypatch):
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({
        "printer": {"ip": "10.0.0.1", "serial_number": "AAA", "model": "P1S"},
    }))
    monkeypatch.setenv("BAMBU_PRINTER_IP", "192.168.1.99")
    monkeypatch.setenv("BAMBU_ACCESS_CODE", "testcode")
    from bambu_forge.config import load_config
    cfg = load_config(config_path=config_file)
    assert cfg.printer_ip == "192.168.1.99"
    assert cfg.printer_serial == "AAA"
    assert cfg.access_code == "testcode"


def test_config_file_values_used_when_no_env(tmp_path, monkeypatch):
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps({
        "printer": {"ip": "10.0.0.1", "serial_number": "BBB", "model": "H2C"},
    }))
    monkeypatch.delenv("BAMBU_PRINTER_IP", raising=False)
    monkeypatch.delenv("BAMBU_ACCESS_CODE", raising=False)
    monkeypatch.delenv("BAMBU_SERIAL_NUMBER", raising=False)
    from bambu_forge.config import load_config
    cfg = load_config(config_path=config_file)
    assert cfg.printer_ip == "10.0.0.1"
    assert cfg.printer_serial == "BBB"
    assert cfg.access_code is None


def test_defaults_when_no_config_file(tmp_path, monkeypatch):
    monkeypatch.delenv("BAMBU_PRINTER_IP", raising=False)
    monkeypatch.delenv("BAMBU_ACCESS_CODE", raising=False)
    from bambu_forge.config import load_config
    cfg = load_config(config_path=tmp_path / "nonexistent.json")
    assert cfg.printer_ip is None
    assert cfg.printer_model is None
    assert cfg.workspace_models_dir.endswith("models/")


def test_save_config(tmp_path):
    from bambu_forge.config import save_printer_config
    config_file = tmp_path / "config.json"
    save_printer_config(config_path=config_file, ip="192.168.1.100", serial_number="CCC", model="H2C")
    data = json.loads(config_file.read_text())
    assert data["printer"]["ip"] == "192.168.1.100"
    assert "access_code" not in data["printer"]


def test_mock_mode(monkeypatch):
    monkeypatch.setenv("BAMBU_FORGE_MOCK", "true")
    from bambu_forge.config import load_config
    cfg = load_config()
    assert cfg.mock_mode is True
