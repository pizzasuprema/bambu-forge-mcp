"""Settings optimizer with priority-based and geometry-aware adjustments."""

from __future__ import annotations

from typing import Any

import numpy as np
import trimesh

from bambu_forge.printer_registry import PrinterRegistry

_PRINTER_MAX_SPEEDS: dict[str, int] = {
    "A1M": 200,
    "P1P": 300,
    "P1S": 300,
    "A1": 300,
    "X1": 500,
    "X1C": 500,
    "X1E": 500,
    "P2S": 500,
    "H2S": 500,
    "H2D": 500,
    "H2C": 500,
    "H2D_Pro": 500,
}


def _compute_geometry_metrics(mesh: trimesh.Trimesh) -> dict[str, Any]:
    bounds = mesh.bounds
    dims = bounds[1] - bounds[0]
    width = float(dims[0])
    depth = float(dims[1])
    height = float(dims[2])

    volume = float(mesh.volume) if mesh.is_volume else float(mesh.convex_hull.volume)

    normals = mesh.face_normals
    z_min = bounds[0][2]
    face_centers = mesh.triangles_center

    downward = normals[:, 2] < 0
    above_bed = face_centers[:, 2] > z_min + 0.5

    overhang_faces = downward & above_bed
    if np.any(overhang_faces):
        nz = normals[overhang_faces, 2]
        overhang_angles = np.degrees(np.arccos(np.clip(nz, -1, 1))) - 90.0
        max_overhang = float(np.max(overhang_angles))
    else:
        max_overhang = 0.0

    xy_max = max(width, depth, 1e-6)
    height_width_ratio = height / xy_max

    return {
        "width": width,
        "depth": depth,
        "height": height,
        "volume": volume,
        "max_overhang_angle": max_overhang,
        "height_width_ratio": height_width_ratio,
        "is_tall_narrow": height_width_ratio > 3,
    }


def optimize_settings(
    mesh_path: str, priority: str, printer_model: str | None = None
) -> dict[str, Any]:
    try:
        mesh = trimesh.load(mesh_path, force="mesh")
    except Exception as exc:
        return {"status": "error", "message": str(exc)}

    if not isinstance(mesh, trimesh.Trimesh) or len(mesh.faces) == 0:
        return {"status": "error", "message": "Could not load a valid mesh"}

    metrics = _compute_geometry_metrics(mesh)
    adjustments: list[str] = []

    settings = {
        "layer_height": 0.20,
        "wall_count": 3,
        "infill_density": 15,
        "infill_pattern": "gyroid",
        "print_speed": 200,
        "outer_wall_speed": 100,
        "support_enabled": False,
        "brim_enabled": False,
    }

    priority = priority.lower()
    if priority == "speed":
        settings.update({
            "layer_height": 0.28,
            "wall_count": 2,
            "infill_density": 10,
            "print_speed": 300,
        })
        adjustments.append("Speed priority: thicker layers, fewer walls, faster speeds")
    elif priority == "quality":
        settings.update({
            "layer_height": 0.12,
            "wall_count": 4,
            "print_speed": 100,
            "outer_wall_speed": 60,
        })
        adjustments.append("Quality priority: finer layers, more walls, slower speeds")
    elif priority == "strength":
        settings.update({
            "wall_count": 5,
            "infill_density": 40,
            "infill_pattern": "cubic",
        })
        adjustments.append("Strength priority: more walls, dense cubic infill")
    elif priority == "material_efficiency":
        settings.update({
            "wall_count": 2,
            "infill_density": 8,
            "brim_enabled": False,
        })
        adjustments.append("Material efficiency: fewer walls, minimal infill")
    elif priority == "silent":
        settings.update({
            "print_speed": 80,
            "outer_wall_speed": 50,
        })
        adjustments.append("Silent priority: reduced speeds for quieter operation")

    if metrics["height_width_ratio"] > 3:
        settings["print_speed"] = int(settings["print_speed"] * 0.8)
        settings["outer_wall_speed"] = int(settings["outer_wall_speed"] * 0.8)
        settings["brim_enabled"] = True
        adjustments.append(
            f"Tall/narrow part (ratio {metrics['height_width_ratio']:.1f}): "
            "reduced speed 20%, enabled brim"
        )

    if metrics["max_overhang_angle"] > 45:
        settings["support_enabled"] = True
        adjustments.append(
            f"Steep overhang detected ({metrics['max_overhang_angle']:.0f}°): "
            "enabled supports"
        )

    if printer_model is not None:
        registry = PrinterRegistry(bambu_studio_path=None)
        printer = registry.get(printer_model)
        if printer is not None:
            max_speed = _PRINTER_MAX_SPEEDS.get(printer_model, 500)
            if settings["print_speed"] > max_speed:
                settings["print_speed"] = max_speed
                adjustments.append(
                    f"Capped print speed to {max_speed}mm/s for {printer.display_name}"
                )
            if settings["outer_wall_speed"] > max_speed:
                settings["outer_wall_speed"] = max_speed
                adjustments.append(
                    f"Capped outer wall speed to {max_speed}mm/s for {printer.display_name}"
                )

            if printer.enclosed:
                adjustments.append(
                    f"{printer.display_name} is enclosed: "
                    "higher temp materials (ABS/ASA) are viable"
                )

            if printer.dual_nozzle:
                adjustments.append(
                    f"{printer.display_name} has dual nozzles: "
                    "consider soluble support material on second nozzle"
                )

    return {
        "status": "success",
        "settings": settings,
        "adjustments": adjustments,
    }
