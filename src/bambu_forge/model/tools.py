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
    db_path: str = "design_dna.db",
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
        db_path = cfg.db_path
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
        db_path = cfg.db_path
        return await list_designs_impl(query=query, db_path=db_path)
