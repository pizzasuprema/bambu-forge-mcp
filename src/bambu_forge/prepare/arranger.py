"""Plate arranger using greedy 2D bin-packing with bounding boxes."""

from __future__ import annotations

import math
from pathlib import Path
from typing import Any

import trimesh


def arrange_plate(
    mesh_paths: list[str],
    strategy: str = "compact",
    build_volume: tuple[int, int, int] = (256, 256, 256),
) -> dict[str, Any]:
    plate_w, plate_h = build_volume[0], build_volume[1]
    gap = 10.0 if strategy == "accessible" else 2.0

    parts: list[dict[str, Any]] = []
    for path in mesh_paths:
        mesh = trimesh.load(path, force="mesh")
        dims = mesh.bounds[1] - mesh.bounds[0]
        parts.append({
            "file": Path(path).name,
            "width": float(dims[0]),
            "depth": float(dims[1]),
        })

    if strategy == "batch" and parts:
        original = parts[0]
        cols = math.floor((plate_w + gap) / (original["width"] + gap))
        rows = math.floor((plate_h + gap) / (original["depth"] + gap))
        fill_count = max(0, cols * rows - 1)
        for _ in range(fill_count):
            parts.append(dict(original))

    parts.sort(key=lambda p: p["width"] * p["depth"], reverse=True)

    placed: list[tuple[float, float, float, float]] = []
    placements: list[dict[str, Any]] = []
    overflow: list[str] = []

    for part in parts:
        pos = _try_place(part["width"], part["depth"], placed, gap, plate_w, plate_h)
        if pos is not None:
            placed.append((pos[0], pos[1], part["width"], part["depth"]))
            placements.append({
                "file": part["file"],
                "position": [round(pos[0], 1), round(pos[1], 1)],
                "fits": True,
            })
        else:
            overflow.append(part["file"])

    placed_area = sum(w * h for _, _, w, h in placed)
    plate_area = plate_w * plate_h
    utilization = round(placed_area / plate_area, 4) if plate_area > 0 else 0.0

    return {
        "status": "success",
        "placements": placements,
        "overflow": overflow,
        "plate_utilization": utilization,
    }


def _try_place(
    w: float,
    h: float,
    placed: list[tuple[float, float, float, float]],
    gap: float,
    plate_w: int,
    plate_h: int,
) -> tuple[float, float] | None:
    max_x = plate_w - w
    max_y = plate_h - h
    if max_x < 0 or max_y < 0:
        return None

    y = 0.0
    while y <= max_y:
        x = 0.0
        while x <= max_x:
            if not _overlaps_any(x, y, w, h, placed, gap):
                return (x, y)
            x += 1.0
        y += 1.0
    return None


def _overlaps_any(
    x: float,
    y: float,
    w: float,
    h: float,
    placed: list[tuple[float, float, float, float]],
    gap: float,
) -> bool:
    for px, py, pw, ph in placed:
        if not (
            x + w + gap <= px
            or px + pw + gap <= x
            or y + h + gap <= py
            or py + ph + gap <= y
        ):
            return True
    return False
