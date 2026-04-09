from __future__ import annotations

from pathlib import Path
from typing import Any

import socket

from fastmcp import FastMCP

from bambu_forge.config import BambuForgeConfig, load_config, save_printer_config
from bambu_forge.printer_registry import PrinterRegistry
from bambu_forge.printer.mqtt_client import BambuMqttClient
from bambu_forge.printer.tools import register_printer_tools
from bambu_forge.profiles.tools import register_profile_tools
from bambu_forge.model.tools import register_model_tools
from bambu_forge.prepare.tools import register_prepare_tools

mcp = FastMCP(
    "bambu-forge",
    instructions="All-in-one MCP server for Bambu Lab 3D printers",
)

_config: BambuForgeConfig | None = None
_registry: PrinterRegistry | None = None
_mqtt_client: BambuMqttClient | None = None


def get_config() -> BambuForgeConfig:
    global _config
    if _config is None:
        _config = load_config()
    return _config


def get_mqtt_client() -> BambuMqttClient:
    global _mqtt_client
    if _mqtt_client is None:
        cfg = get_config()
        _mqtt_client = BambuMqttClient(
            host=cfg.printer_ip or "127.0.0.1",
            access_code=cfg.access_code or "",
            serial=cfg.printer_serial or "",
            mock=cfg.mock_mode,
        )
        _mqtt_client.connect()
    return _mqtt_client


def get_registry() -> PrinterRegistry:
    global _registry
    if _registry is None:
        cfg = get_config()
        studio_path = None
        if cfg.bambu_studio_path:
            candidate = Path(cfg.bambu_studio_path).parent.parent / "Resources"
            if not candidate.exists():
                candidate = Path.home() / "Library/Application Support/BambuStudio"
            if candidate.exists():
                studio_path = candidate
        else:
            default = Path.home() / "Library/Application Support/BambuStudio"
            if default.exists():
                studio_path = default
        _registry = PrinterRegistry(bambu_studio_path=studio_path)
    return _registry


@mcp.tool()
async def ping() -> dict:
    """Health check — returns server version, config status, and printer registry status."""
    from bambu_forge import __version__

    cfg = get_config()
    reg = get_registry()
    printer = reg.get(cfg.printer_model) if cfg.printer_model else None
    return {
        "status": "ok",
        "version": __version__,
        "mock_mode": cfg.mock_mode,
        "printer_model": cfg.printer_model,
        "printer_found": printer is not None,
        "registry_models": len(reg.list_models()),
    }


register_printer_tools(mcp, get_config, get_registry, get_mqtt_client)
register_profile_tools(mcp, get_config)
register_model_tools(mcp, get_config)
register_prepare_tools(mcp, get_config)


@mcp.tool()
async def discover_printers(mock: bool = False, timeout: int = 5) -> dict[str, Any]:
    """Discover Bambu printers on the LAN via SSDP, or return mock printers when ``mock`` is true."""
    from bambu_forge.printer.discovery import discover_printers as discover_printers_impl

    printers = discover_printers_impl(mock=mock, timeout=float(timeout))
    return {"status": "success", "printers": printers, "count": len(printers)}


@mcp.tool()
async def setup_printer(printer_ip: str) -> dict[str, Any]:
    """Discover or verify a printer at ``printer_ip`` and persist IP, serial, and model to config."""
    from bambu_forge.printer.discovery import discover_printers as discover_printers_impl

    cfg = get_config()
    config_path = Path.home() / ".bambu-forge" / "config.json"
    printers = discover_printers_impl(mock=cfg.mock_mode, timeout=5.0)

    entry = next((p for p in printers if p.get("ip") == printer_ip), None)
    if entry is None and cfg.mock_mode and printers:
        entry = {**printers[0], "ip": printer_ip}

    if entry is None:
        try:
            with socket.create_connection((printer_ip, 8883), timeout=3.0):
                pass
        except OSError:
            return {
                "status": "error",
                "error_code": "PRINTER_NOT_FOUND",
                "message": f"No SSDP match for {printer_ip} and MQTT port unreachable",
            }
        entry = {
            "ip": printer_ip,
            "serial": "UNKNOWN",
            "model": "UNKNOWN",
            "name": "",
            "firmware": "",
            "signal": "",
        }

    save_printer_config(
        config_path,
        entry["ip"],
        entry["serial"],
        entry["model"],
    )
    global _config
    _config = None

    return {
        "status": "success",
        "message": "Printer configuration saved",
        "printer_ip": entry["ip"],
        "serial": entry["serial"],
        "model": entry["model"],
        "name": entry.get("name", ""),
        "firmware": entry.get("firmware", ""),
        "signal": entry.get("signal", ""),
    }


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
