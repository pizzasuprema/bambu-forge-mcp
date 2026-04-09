import trimesh

from bambu_forge.prepare.cost_estimator import estimate_cost


def test_estimate_from_mesh(tmp_path):
    """Volume-based estimation from a box mesh should populate all cost fields."""
    mesh = trimesh.primitives.Box(extents=(20, 20, 20))
    mesh_path = tmp_path / "box.stl"
    mesh.export(str(mesh_path))

    result = estimate_cost(mesh_path=str(mesh_path))

    assert result["status"] == "success"
    data = result["data"]
    assert data["is_estimate"] is True
    assert data["filament_grams"] > 0
    assert data["print_time_minutes"] > 0
    assert data["filament_cost"] > 0
    assert data["power_cost"] > 0
    assert "printer_cost" in data
    assert data["total_cost"] > 0


def test_estimate_from_sliced_data():
    """Sliced-data mode should use provided values directly, not estimate."""
    sliced = {"filament_grams": 50.0, "print_time": 120}

    result = estimate_cost(sliced_data=sliced)

    assert result["status"] == "success"
    data = result["data"]
    assert data["is_estimate"] is False
    assert data["filament_grams"] == 50.0
    assert data["print_time_minutes"] == 120


def test_cost_math():
    """100g filament at $25/kg should cost exactly $2.50 in material."""
    sliced = {"filament_grams": 100.0, "print_time": 60}

    result = estimate_cost(
        sliced_data=sliced,
        filament_price_per_kg=25.0,
        electricity_rate_kwh=0.12,
        printer_hourly_rate=0.0,
    )

    data = result["data"]
    assert abs(data["filament_cost"] - 2.50) < 0.01
    expected_power = 1.0 * 0.2 * 0.12  # 1 hour * 0.2kW * $0.12/kWh
    assert abs(data["power_cost"] - expected_power) < 0.01
    assert abs(data["total_cost"] - (2.50 + expected_power)) < 0.01
