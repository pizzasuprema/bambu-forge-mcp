"""MCP tools for model slicing and printability analysis."""

from __future__ import annotations

from typing import Any

from bambu_forge.prepare.slicer import run_slicer


def register_prepare_tools(mcp, get_config, get_registry=None):
    @mcp.tool()
    async def slice_model(
        input_file: str,
        output_file: str,
        machine_settings: str | None = None,
        process_settings: str | None = None,
        filament_settings: str | None = None,
        plate_index: int = 0,
    ) -> dict[str, Any]:
        """Slice a 3D model (STL) into a print-ready 3MF using Bambu Studio CLI."""
        cfg = get_config()
        slicer_path = cfg.bambu_studio_path or ""
        mock = cfg.mock_mode

        result = run_slicer(
            slicer_path=slicer_path,
            input_file=input_file,
            output_file=output_file,
            machine_settings=machine_settings,
            process_settings=process_settings,
            filament_settings=filament_settings,
            plate_index=plate_index,
            mock=mock,
        )
        return result

    @mcp.tool()
    async def analyze_printability(file_path: str) -> dict[str, Any]:
        """Analyze a 3D model for printability issues (overhangs, thin walls, bridging, adhesion, supports, warping, thermal stress)."""
        cfg = get_config()
        from bambu_forge.prepare.analyzer import analyze_printability as _analyze

        return _analyze(file_path, printer_model=cfg.printer_model)

    @mcp.tool()
    async def optimize_settings(file_path: str, priorities: str) -> dict[str, Any]:
        """Optimize print settings for a 3D model based on priority (speed, quality, strength, material_efficiency, silent)."""
        cfg = get_config()
        from bambu_forge.prepare.optimizer import optimize_settings as _optimize

        return _optimize(file_path, priority=priorities, printer_model=cfg.printer_model)

    @mcp.tool()
    async def estimate_cost(
        file_path: str, profile_name: str | None = None
    ) -> dict[str, Any]:
        """Estimate print cost (filament, power, time) from a 3D model or sliced output."""
        cfg = get_config()
        from bambu_forge.prepare.cost_estimator import estimate_cost as _estimate

        result = _estimate(
            mesh_path=file_path,
            electricity_rate_kwh=cfg.electricity_rate_kwh,
            printer_hourly_rate=cfg.printer_hourly_rate,
        )
        if profile_name is not None and result.get("status") == "success":
            result["profile_name"] = profile_name
        return result

    @mcp.tool()
    async def arrange_plate(
        file_paths: str, strategy: str = "compact"
    ) -> dict[str, Any]:
        """Arrange multiple 3D models on a build plate using bin-packing (compact, accessible, or batch strategy)."""
        import json as _json

        from bambu_forge.prepare.arranger import arrange_plate as _arrange

        try:
            paths = _json.loads(file_paths)
        except (_json.JSONDecodeError, TypeError):
            paths = [p.strip() for p in file_paths.split(",") if p.strip()]

        if not isinstance(paths, list):
            paths = [paths]

        build_volume = (256, 256, 256)
        cfg = get_config()
        if get_registry is not None and cfg.printer_model:
            printer = get_registry().get(cfg.printer_model)
            if printer is not None:
                build_volume = tuple(printer.build_volume)

        return _arrange(paths, strategy=strategy, build_volume=build_volume)

    @mcp.tool()
    async def export_project(
        file_paths: str, output_path: str, profile_name: str | None = None
    ) -> dict[str, Any]:
        """Export a complete 3MF project with models, profiles, and plate layout (planned for future release)."""
        return {
            "status": "error",
            "error_code": "NOT_IMPLEMENTED",
            "message": "export_project is planned for a future release",
        }
