"""Validate mesh files (e.g. STL) for printability using trimesh."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import numpy as np
import trimesh


@dataclass
class MeshValidationResult:
    valid: bool
    triangle_count: int = 0
    bounding_box: tuple[tuple[float, float, float], tuple[float, float, float]] | None = None
    volume: float = 0.0
    is_watertight: bool = False
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def validate_mesh(file_path: str) -> MeshValidationResult:
    path = Path(file_path)
    if not path.is_file():
        return MeshValidationResult(
            valid=False,
            errors=["Fatal: file does not exist or is not a file"],
        )

    if path.stat().st_size == 0:
        return MeshValidationResult(
            valid=False,
            errors=["Fatal: file is empty"],
        )

    try:
        loaded = trimesh.load(str(path), force="mesh")
    except Exception as exc:  # noqa: BLE001 — surface parse/load failures to caller
        return MeshValidationResult(
            valid=False,
            errors=[f"Parse error: {exc}"],
        )

    if loaded is None:
        return MeshValidationResult(
            valid=False,
            errors=["Parse error: load returned no mesh data"],
        )

    mesh: trimesh.Trimesh
    if isinstance(loaded, trimesh.Scene):
        try:
            mesh = loaded.dump(concatenate=True)
        except Exception as exc:  # noqa: BLE001
            return MeshValidationResult(
                valid=False,
                errors=[f"Parse error: could not combine scene geometry ({exc})"],
            )
    elif isinstance(loaded, trimesh.Trimesh):
        mesh = loaded
    else:
        return MeshValidationResult(
            valid=False,
            errors=["Parse error: loaded object is not a mesh"],
        )

    faces = getattr(mesh, "faces", None)
    if faces is None or len(faces) == 0:
        return MeshValidationResult(
            valid=False,
            errors=["Fatal: mesh has no faces"],
        )

    is_watertight = bool(mesh.is_watertight)
    warnings: list[str] = []
    if not is_watertight:
        warnings.append("Mesh is not watertight (may not be manifold)")

    bounds = np.asarray(mesh.bounds, dtype=float)
    extents = bounds[1] - bounds[0]
    if np.any(extents > 1000.0):
        warnings.append(
            "Mesh bounding box exceeds 1000 mm on at least one axis "
            f"(extents: {extents.tolist()} mm)"
        )

    bbox = (
        tuple(float(x) for x in bounds[0]),
        tuple(float(x) for x in bounds[1]),
    )
    volume = float(mesh.volume) if is_watertight else 0.0

    return MeshValidationResult(
        valid=True,
        triangle_count=int(len(faces)),
        bounding_box=bbox,
        volume=volume,
        is_watertight=is_watertight,
        errors=[],
        warnings=warnings,
    )
