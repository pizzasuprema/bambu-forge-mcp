"""MCP tools for model slicing and printability analysis."""

from __future__ import annotations

from typing import Any

from bambu_forge.prepare.slicer import run_slicer


def register_prepare_tools(mcp, get_config):
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
        from bambu_forge.prepare.cost_estimator import estimate_cost as _estimate

        return _estimate(mesh_path=file_path)
