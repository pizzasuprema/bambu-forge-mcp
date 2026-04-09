"""Mesh modification and boolean combination operations."""

from __future__ import annotations

import numpy as np
import trimesh


def modify_model(
    mesh_path: str, operations: list[dict], output_path: str
) -> dict:
    """Apply sequential operations to a mesh. Returns result dict."""
    try:
        mesh = trimesh.load(mesh_path, force="mesh")
    except Exception as e:
        return {"status": "error", "error_code": "MESH_LOAD_FAILED", "message": str(e)}

    applied: list[str] = []
    for op in operations:
        op_type = op.get("type")
        if op_type == "scale":
            mesh.apply_scale(op["factor"])
        elif op_type == "scale_axis":
            scale = [1.0, 1.0, 1.0]
            scale[{"x": 0, "y": 1, "z": 2}[op["axis"]]] = op["factor"]
            mesh.apply_scale(scale)
        elif op_type == "mirror":
            axis_idx = {"x": 0, "y": 1, "z": 2}[op["axis"]]
            matrix = np.eye(4)
            matrix[axis_idx, axis_idx] = -1
            mesh.apply_transform(matrix)
        elif op_type == "rotate":
            angle = np.radians(op["degrees"])
            axis_idx = {"x": 0, "y": 1, "z": 2}[op["axis"]]
            axis_vec = [0.0, 0.0, 0.0]
            axis_vec[axis_idx] = 1.0
            matrix = trimesh.transformations.rotation_matrix(angle, axis_vec)
            mesh.apply_transform(matrix)
        elif op_type == "translate":
            mesh.apply_translation([op.get("x", 0), op.get("y", 0), op.get("z", 0)])
        elif op_type == "cut":
            plane_normal = {"xy": [0, 0, 1], "xz": [0, 1, 0], "yz": [1, 0, 0]}[
                op["plane"]
            ]
            plane_origin = [0.0, 0.0, 0.0]
            plane_origin[{"xy": 2, "xz": 1, "yz": 0}[op["plane"]]] = op["offset"]
            if op.get("keep") == "above":
                plane_normal = [-n for n in plane_normal]
            mesh = trimesh.intersections.slice_mesh_plane(
                mesh, plane_normal, plane_origin
            )
        else:
            return {"status": "error", "message": f"Unknown operation: {op_type}"}
        applied.append(op_type)

    mesh.export(output_path)
    return {
        "status": "success",
        "file_path": output_path,
        "operations_applied": applied,
        "triangle_count": len(mesh.faces),
    }


def combine_models(
    file_a: str, file_b: str, operation: str, output_path: str
) -> dict:
    """Boolean operation on two meshes."""
    try:
        mesh_a = trimesh.load(file_a, force="mesh")
        mesh_b = trimesh.load(file_b, force="mesh")
    except Exception as e:
        return {"status": "error", "error_code": "MESH_LOAD_FAILED", "message": str(e)}

    if operation not in ("union", "difference", "intersection"):
        return {
            "status": "error",
            "message": f"Unknown operation: {operation}. Use union, difference, or intersection.",
        }

    try:
        bool_fn = getattr(trimesh.boolean, operation)
        result = bool_fn([mesh_a, mesh_b])
    except Exception as e:
        return {
            "status": "error",
            "message": f"Boolean operation failed: {e}. Both meshes must be watertight.",
        }

    result.export(output_path)
    return {
        "status": "success",
        "file_path": output_path,
        "triangle_count": len(result.faces),
    }
