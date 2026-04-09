"""7-dimension printability analyzer with Bambu-specific checks."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import numpy as np
import trimesh

from bambu_forge.printer_registry import PrinterRegistry


def analyze_printability(
    mesh_path: str, printer_model: str | None = None
) -> dict[str, Any]:
    try:
        mesh = trimesh.load(mesh_path, force="mesh")
    except Exception as exc:
        return {"status": "error", "message": str(exc)}

    if not isinstance(mesh, trimesh.Trimesh) or len(mesh.faces) == 0:
        return {"status": "error", "message": "Could not load a valid mesh"}

    dimensions = {
        "overhangs": _score_overhangs(mesh),
        "thin_walls": _score_thin_walls(mesh),
        "bridging": _score_bridging(mesh),
        "bed_adhesion": _score_bed_adhesion(mesh),
        "supports": _score_supports(mesh),
        "warping": _score_warping(mesh, enclosed=False),
        "thermal_stress": _score_thermal_stress(mesh),
    }

    bambu_specific: dict[str, Any] = {}
    if printer_model is not None:
        registry = PrinterRegistry(bambu_studio_path=None)
        printer = registry.get(printer_model)
        if printer is not None:
            dimensions["warping"] = _score_warping(mesh, enclosed=printer.enclosed)
            bambu_specific = _bambu_checks(mesh, printer)

    overall = int(np.mean([d["score"] for d in dimensions.values()]))
    return {
        "status": "success",
        "overall_score": overall,
        "dimensions": dimensions,
        "bambu_specific": bambu_specific,
    }


def _score_overhangs(mesh: trimesh.Trimesh) -> dict[str, Any]:
    normals = mesh.face_normals
    up = np.array([0.0, 0.0, 1.0])
    cos_angles = normals @ up
    overhang_threshold = np.cos(np.radians(45))
    downward = normals[:, 2] < 0
    overhang_mask = downward & (cos_angles < -overhang_threshold)
    overhang_pct = float(np.sum(overhang_mask)) / max(len(normals), 1)
    score = max(0, min(100, int(100 - overhang_pct * 100)))

    recs: list[str] = []
    if overhang_pct > 0.1:
        recs.append(
            f"{overhang_pct:.0%} of faces are steep overhangs (>45deg). Consider reorienting or adding supports."
        )
    return {"score": score, "recommendations": recs}


def _score_thin_walls(mesh: trimesh.Trimesh) -> dict[str, Any]:
    min_wall = 0.4
    try:
        points, face_idx = trimesh.sample.sample_surface(mesh, count=500)
    except Exception:
        return {"score": 100, "recommendations": []}

    sample_normals = mesh.face_normals[face_idx]
    inward = -sample_normals
    origins = points + inward * 1e-4

    locations, ray_idx, _ = mesh.ray.intersects_location(origins, inward)

    thin_count = 0
    for i in range(len(origins)):
        hits = locations[ray_idx == i]
        if len(hits) > 0:
            dists = np.linalg.norm(hits - origins[i], axis=1)
            thickness = float(np.min(dists))
            if thickness < min_wall:
                thin_count += 1

    thin_pct = thin_count / max(len(origins), 1)
    score = max(0, min(100, int(100 - thin_pct * 100)))
    recs: list[str] = []
    if thin_pct > 0.05:
        recs.append(
            f"{thin_pct:.0%} of sampled points have wall thickness < {min_wall}mm. "
            "Consider increasing wall thickness."
        )
    return {"score": score, "recommendations": recs}


def _score_bridging(mesh: trimesh.Trimesh) -> dict[str, Any]:
    max_bridge = 10.0
    normals = mesh.face_normals
    horizontal_mask = np.abs(normals[:, 2]) < 0.1
    horizontal_faces = np.where(horizontal_mask)[0]

    if len(horizontal_faces) == 0:
        return {"score": 100, "recommendations": []}

    edges_of_horizontal = set()
    for fi in horizontal_faces:
        face = mesh.faces[fi]
        for j in range(3):
            edge = tuple(sorted((face[j], face[(j + 1) % 3])))
            edges_of_horizontal.add(edge)

    bridge_lengths: list[float] = []
    for e in edges_of_horizontal:
        v0, v1 = mesh.vertices[e[0]], mesh.vertices[e[1]]
        mid = (v0 + v1) / 2.0
        if mid[2] > mesh.bounds[0][2] + 0.5:
            length = float(np.linalg.norm(v1 - v0))
            bridge_lengths.append(length)

    if not bridge_lengths:
        return {"score": 100, "recommendations": []}

    longest = max(bridge_lengths)
    score = max(0, min(100, int(100 - (longest / max_bridge) * 100)))
    recs: list[str] = []
    if longest > max_bridge:
        recs.append(
            f"Detected potential bridge span of {longest:.1f}mm (limit ~{max_bridge}mm). "
            "Consider adding supports or redesigning."
        )
    return {"score": score, "recommendations": recs}


def _score_bed_adhesion(mesh: trimesh.Trimesh) -> dict[str, Any]:
    bounds = mesh.bounds
    z_min = bounds[0][2]
    tolerance = 0.1

    bed_faces_mask = np.any(
        mesh.vertices[mesh.faces][:, :, 2] <= z_min + tolerance, axis=1
    )
    bed_face_area = float(np.sum(mesh.area_faces[bed_faces_mask]))
    footprint_area = (bounds[1][0] - bounds[0][0]) * (bounds[1][1] - bounds[0][1])
    part_height = bounds[1][2] - bounds[0][2]

    if footprint_area < 1e-6:
        return {"score": 50, "recommendations": ["Part has near-zero footprint."]}

    contact_ratio = bed_face_area / max(footprint_area, 1e-6)
    height_ratio = part_height / max(np.sqrt(footprint_area), 1e-6)

    score = 100
    if height_ratio > 3:
        score -= int(min(40, height_ratio * 5))
    if contact_ratio < 0.3:
        score -= int(min(30, (1 - contact_ratio) * 30))
    score = max(0, min(100, score))

    recs: list[str] = []
    if height_ratio > 3:
        recs.append(
            f"Tall narrow part (height/base ratio {height_ratio:.1f}). Consider adding a brim or raft."
        )
    if contact_ratio < 0.3:
        recs.append("Low bed contact area. Consider a brim for better adhesion.")
    return {"score": score, "recommendations": recs}


def _score_supports(mesh: trimesh.Trimesh) -> dict[str, Any]:
    normals = mesh.face_normals
    up = np.array([0.0, 0.0, 1.0])
    cos_angles = normals @ up
    overhang_threshold = np.cos(np.radians(45))
    downward = normals[:, 2] < 0
    overhang_mask = downward & (cos_angles < -overhang_threshold)

    overhang_area = float(np.sum(mesh.area_faces[overhang_mask]))
    bounds = mesh.bounds
    avg_height = (bounds[1][2] - bounds[0][2]) / 2.0
    estimated_support_volume = overhang_area * max(avg_height, 0.1)
    part_volume = float(mesh.volume) if mesh.is_volume else float(mesh.convex_hull.volume)
    ratio = estimated_support_volume / max(part_volume, 1e-6)

    score = max(0, min(100, int(100 - ratio * 100)))
    recs: list[str] = []
    if ratio > 0.2:
        recs.append(
            f"Estimated support volume is {ratio:.0%} of part volume. "
            "Consider reorienting to reduce supports."
        )
    return {"score": score, "recommendations": recs}


def _score_warping(mesh: trimesh.Trimesh, enclosed: bool = False) -> dict[str, Any]:
    bounds = mesh.bounds
    dims = bounds[1] - bounds[0]
    max_dim = float(np.max(dims))
    min_dim = float(np.min(dims[dims > 1e-6])) if np.any(dims > 1e-6) else 1.0
    aspect_ratio = max_dim / max(min_dim, 1e-6)
    volume = float(mesh.volume) if mesh.is_volume else float(mesh.convex_hull.volume)

    score = 100
    if aspect_ratio > 5:
        score -= int(min(30, (aspect_ratio - 5) * 5))
    if volume > 100_000:
        score -= int(min(30, (volume / 100_000) * 10))
    if enclosed:
        score = min(100, score + 15)
    score = max(0, min(100, score))

    recs: list[str] = []
    if aspect_ratio > 5:
        recs.append(
            f"High aspect ratio ({aspect_ratio:.1f}). Long flat parts are prone to warping."
        )
    if not enclosed:
        recs.append("Printer is not enclosed. Consider using an enclosure to reduce warping.")
    return {"score": score, "recommendations": recs}


def _score_thermal_stress(mesh: trimesh.Trimesh) -> dict[str, Any]:
    if not hasattr(mesh, "face_adjacency_angles") or len(mesh.face_adjacency_angles) == 0:
        return {"score": 100, "recommendations": []}

    angles = mesh.face_adjacency_angles
    sharp_threshold = np.radians(60)
    sharp_count = int(np.sum(angles > sharp_threshold))
    sharp_pct = sharp_count / max(len(angles), 1)

    score = max(0, min(100, int(100 - sharp_pct * 100)))
    recs: list[str] = []
    if sharp_pct > 0.1:
        recs.append(
            f"{sharp_pct:.0%} of face adjacencies have sharp dihedral angles (>60deg). "
            "These areas may concentrate thermal stress."
        )
    return {"score": score, "recommendations": recs}


def _bambu_checks(mesh: trimesh.Trimesh, printer: Any) -> dict[str, Any]:
    bounds = mesh.bounds
    dims = bounds[1] - bounds[0]
    bv = printer.build_volume
    margin = [float(bv[i] - dims[i]) for i in range(3)]
    fits = all(m >= 0 for m in margin)

    material_warnings: list[str] = []
    if not printer.enclosed:
        material_warnings.append(
            "Printer is not enclosed. ABS/ASA may warp — consider PLA or PETG."
        )

    dual_recs: list[str] = []
    if printer.dual_nozzle:
        dual_recs.append(
            "Dual-nozzle printer detected. Consider soluble PVA supports for complex overhangs."
        )

    return {
        "fits_build_volume": fits,
        "build_volume_margin": margin,
        "material_warnings": material_warnings,
        "dual_nozzle_recommendations": dual_recs,
    }
