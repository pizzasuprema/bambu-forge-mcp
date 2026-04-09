from __future__ import annotations
import json
import os
from dataclasses import dataclass
from pathlib import Path

_DEFAULT_BASE = Path.home() / ".bambu-forge"


def _dir_under_base(name: str) -> str:
    """POSIX str(Path(.../name/)) drops trailing slash; callers expect dir paths to end with /."""
    return str(_DEFAULT_BASE / name) + "/"


_DEFAULT_CERTS = _dir_under_base("certs")
_DEFAULT_MODELS = _dir_under_base("models")
_DEFAULT_EXPORTS = _dir_under_base("exports")


@dataclass
class BambuForgeConfig:
    printer_ip: str | None = None
    printer_serial: str | None = None
    printer_model: str | None = None
    access_code: str | None = None
    cert_path: str = _DEFAULT_CERTS
    bambu_studio_path: str | None = None
    orca_slicer_path: str | None = None
    prefer_orca: bool = False
    workspace_models_dir: str = _DEFAULT_MODELS
    workspace_exports_dir: str = _DEFAULT_EXPORTS
    db_path: str = str(_DEFAULT_BASE / "profiles.db")
    design_db_path: str = str(_DEFAULT_BASE / "designs.db")
    electricity_rate_kwh: float = 0.12
    printer_hourly_rate: float = 0.00
    mock_mode: bool = False

def load_config(config_path: Path | None = None) -> BambuForgeConfig:
    if config_path is None:
        config_path = _DEFAULT_BASE / "config.json"
    file_data: dict = {}
    if config_path.exists():
        with open(config_path) as f:
            file_data = json.load(f)
    printer = file_data.get("printer", {})
    slicer = file_data.get("slicer", {})
    workspace = file_data.get("workspace", {})
    cost = file_data.get("cost", {})
    return BambuForgeConfig(
        printer_ip=os.environ.get("BAMBU_PRINTER_IP") or printer.get("ip"),
        printer_serial=os.environ.get("BAMBU_SERIAL_NUMBER") or printer.get("serial_number"),
        printer_model=os.environ.get("BAMBU_PRINTER_MODEL") or printer.get("model"),
        access_code=os.environ.get("BAMBU_ACCESS_CODE"),
        cert_path=printer.get("cert_path", _DEFAULT_CERTS),
        bambu_studio_path=slicer.get("bambu_studio_path"),
        orca_slicer_path=slicer.get("orca_slicer_path"),
        prefer_orca=slicer.get("prefer_orca", False),
        workspace_models_dir=workspace.get("models_dir", _DEFAULT_MODELS),
        workspace_exports_dir=workspace.get("exports_dir", _DEFAULT_EXPORTS),
        db_path=workspace.get("db_path", str(_DEFAULT_BASE / "profiles.db")),
        design_db_path=workspace.get("design_db_path", str(_DEFAULT_BASE / "designs.db")),
        electricity_rate_kwh=cost.get("electricity_rate_kwh", 0.12),
        printer_hourly_rate=cost.get("printer_hourly_rate", 0.00),
        mock_mode=os.environ.get("BAMBU_FORGE_MOCK", "").lower() == "true",
    )

def save_printer_config(config_path: Path, ip: str, serial_number: str, model: str) -> None:
    existing: dict = {}
    if config_path.exists():
        with open(config_path) as f:
            existing = json.load(f)
    existing.setdefault("printer", {})
    existing["printer"]["ip"] = ip
    existing["printer"]["serial_number"] = serial_number
    existing["printer"]["model"] = model
    config_path.parent.mkdir(parents=True, exist_ok=True)
    with open(config_path, "w") as f:
        json.dump(existing, f, indent=2)
