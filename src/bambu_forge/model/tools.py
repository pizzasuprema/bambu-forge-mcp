"""MCP tools for model generation and design management."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from bambu_forge.mesh_validator import validate_mesh
from bambu_forge.model.cad_engine import execute_cadquery
from bambu_forge.model.design_dna import DesignDnaStore


async def generate_model_impl(
    code: str,
    output_name: str,
    workspace: str,
    db_path: str,
    timeout: int = 60,
    parent_id: int | None = None,
) -> dict[str, Any]:
    ws = Path(workspace)
    ws.mkdir(parents=True, exist_ok=True)

    if not output_name.endswith(".stl"):
        output_name += ".stl"
    output_path = str(ws / output_name)

    result = execute_cadquery(code, output_path, workspace, timeout=timeout)
    if not result["success"]:
        return {"status": "error", "error": result["error"]}

    validation = validate_mesh(output_path)

    store = DesignDnaStore(db_path=db_path)
    try:
        bbox = list(validation.bounding_box) if validation.bounding_box else []
        design_id = store.save(
            name=output_name.removesuffix(".stl"),
            source_type="cadquery",
            source_code=code,
            mesh_path=output_path,
            bbox=bbox,
            volume=validation.volume,
            triangle_count=validation.triangle_count,
            parent_id=parent_id,
        )
    finally:
        store.close()

    return {
        "status": "success",
        "design_id": design_id,
        "mesh_path": output_path,
        "triangle_count": validation.triangle_count,
        "volume": validation.volume,
        "valid": validation.valid,
        "is_watertight": validation.is_watertight,
        "warnings": validation.warnings,
    }


async def list_designs_impl(
    query: str | None = None,
    db_path: str = str(Path.home() / ".bambu-forge" / "designs.db"),
) -> dict[str, Any]:
    store = DesignDnaStore(db_path=db_path)
    try:
        designs = store.list_designs(query=query)
        return {"status": "success", "data": designs, "count": len(designs)}
    finally:
        store.close()


def register_model_tools(mcp, get_config):
    @mcp.tool()
    async def generate_model(
        code: str,
        output_name: str = "model",
    ) -> dict[str, Any]:
        """Generate a 3D model from CadQuery code and save to the Design DNA store."""
        cfg = get_config()
        workspace = cfg.workspace_models_dir
        db_path = cfg.design_db_path
        return await generate_model_impl(
            code=code,
            output_name=output_name,
            workspace=workspace,
            db_path=db_path,
        )

    @mcp.tool()
    async def list_designs(query: str | None = None) -> dict[str, Any]:
        """List saved designs from the Design DNA store, optionally filtered by search query."""
        cfg = get_config()
        db_path = cfg.design_db_path
        return await list_designs_impl(query=query, db_path=db_path)

    @mcp.tool()
    async def generate_model_ai(
        description: str,
        style: str = "realistic",
    ) -> dict[str, Any]:
        """Submit an AI text-to-3D generation job. Returns a job_id to poll with check_generation."""
        from bambu_forge.model.ai_generator import submit_generation

        cfg = get_config()
        return await submit_generation(
            description=description, style=style, mock=cfg.mock_mode
        )

    @mcp.tool()
    async def check_generation_status(job_id: str) -> dict[str, Any]:
        """Check status of an AI generation job. Downloads mesh on completion."""
        from bambu_forge.model.ai_generator import check_generation

        cfg = get_config()
        return await check_generation(
            job_id=job_id, workspace=cfg.workspace_models_dir, mock=cfg.mock_mode
        )

    @mcp.tool()
    async def modify_model_tool(
        file_path: str,
        operations: str,
    ) -> dict[str, Any]:
        """Apply operations (scale, rotate, mirror, translate, cut) to a mesh. operations is a JSON array."""
        from bambu_forge.model.stl_ops import modify_model

        cfg = get_config()
        ops = json.loads(operations)
        output_path = str(
            Path(cfg.workspace_models_dir) / Path(file_path).stem
        ) + "_modified.stl"
        return modify_model(file_path, ops, output_path)

    @mcp.tool()
    async def combine_models_tool(
        file_a: str,
        file_b: str,
        operation: str = "union",
    ) -> dict[str, Any]:
        """Boolean operation (union, difference, intersection) on two meshes."""
        from bambu_forge.model.stl_ops import combine_models

        cfg = get_config()
        output_path = str(
            Path(cfg.workspace_models_dir) / "combined.stl"
        )
        return combine_models(file_a, file_b, operation, output_path)

    @mcp.tool()
    async def generate_2d_pattern_tool(
        code: str,
        output_format: str = "svg",
    ) -> dict[str, Any]:
        """Generate a 2D pattern (SVG or DXF) from user code for laser cutting."""
        from bambu_forge.model.pattern_2d import generate_2d_pattern

        cfg = get_config()
        ws = Path(cfg.workspace_models_dir)
        ws.mkdir(parents=True, exist_ok=True)
        output_path = str(ws / f"pattern.{output_format}")
        return generate_2d_pattern(code, output_format, output_path, str(ws))

    @mcp.tool()
    async def search_marketplace_tool(query: str) -> dict[str, Any]:
        """Search MakerWorld for printable 3D models matching a query."""
        from bambu_forge.model.marketplace import search_marketplace

        cfg = get_config()
        return await search_marketplace(query, mock=cfg.mock_mode)
