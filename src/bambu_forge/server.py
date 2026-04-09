from __future__ import annotations

from pathlib import Path

from fastmcp import FastMCP

from bambu_forge.config import BambuForgeConfig, load_config
from bambu_forge.printer_registry import PrinterRegistry

mcp = FastMCP(
    "bambu-forge",
    instructions="All-in-one MCP server for Bambu Lab 3D printers",
)

_config: BambuForgeConfig | None = None
_registry: PrinterRegistry | None = None


def get_config() -> BambuForgeConfig:
    global _config
    if _config is None:
        _config = load_config()
    return _config


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


def main():
    mcp.run(transport="stdio")


if __name__ == "__main__":
    main()
