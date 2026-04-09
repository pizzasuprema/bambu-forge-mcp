"""Cost estimator with sliced-data and volume-based estimation modes."""

from __future__ import annotations

from typing import Any

import trimesh


def estimate_cost(
    mesh_path: str | None = None,
    sliced_data: dict | None = None,
    filament_price_per_kg: float = 25.0,
    electricity_rate_kwh: float = 0.12,
    printer_hourly_rate: float = 0.0,
    infill_percent: int = 15,
    material_density: float = 1.24,
) -> dict[str, Any]:
    if sliced_data is not None:
        weight_g = float(sliced_data["filament_grams"])
        print_time_min = int(sliced_data["print_time"])
        is_estimate = False
    elif mesh_path is not None:
        weight_g, print_time_min = _estimate_from_mesh(
            mesh_path, infill_percent, material_density
        )
        is_estimate = True
    else:
        return {"status": "error", "message": "Provide either mesh_path or sliced_data"}

    print_time_hours = print_time_min / 60.0
    filament_cost = weight_g / 1000.0 * filament_price_per_kg
    power_cost = print_time_hours * 0.2 * electricity_rate_kwh
    printer_cost = print_time_hours * printer_hourly_rate
    total_cost = filament_cost + power_cost + printer_cost

    return {
        "status": "success",
        "data": {
            "filament_grams": round(weight_g, 2),
            "print_time_minutes": print_time_min,
            "filament_cost": round(filament_cost, 4),
            "power_cost": round(power_cost, 4),
            "printer_cost": round(printer_cost, 4),
            "total_cost": round(total_cost, 4),
            "is_estimate": is_estimate,
        },
    }


def _estimate_from_mesh(
    mesh_path: str,
    infill_percent: int,
    material_density: float,
) -> tuple[float, int]:
    mesh = trimesh.load(mesh_path, force="mesh")

    volume_mm3 = float(mesh.volume) if mesh.is_volume else float(mesh.convex_hull.volume)
    volume_cm3 = volume_mm3 / 1000.0

    shell_thickness_mm = 1.2  # ~3 walls × 0.4mm nozzle
    shell_volume_cm3 = (float(mesh.area) * shell_thickness_mm) / 1000.0

    interior_cm3 = max(0.0, volume_cm3 - shell_volume_cm3)
    infill_cm3 = interior_cm3 * (infill_percent / 100.0)

    total_material_cm3 = shell_volume_cm3 + infill_cm3
    weight_g = total_material_cm3 * material_density

    print_time_min = max(1, int(weight_g * 4))
    return weight_g, print_time_min
