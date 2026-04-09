import trimesh

from bambu_forge.prepare.optimizer import optimize_settings


def test_speed_priority(tmp_path):
    """Speed priority should yield thick layers (>= 0.28mm) for faster printing."""
    mesh = trimesh.primitives.Box(extents=(20, 20, 20))
    mesh_path = tmp_path / "box.stl"
    mesh.export(str(mesh_path))

    result = optimize_settings(str(mesh_path), priority="speed")

    assert result["status"] == "success"
    assert result["settings"]["layer_height"] >= 0.28
    assert result["settings"]["print_speed"] >= 200
    assert isinstance(result["adjustments"], list)
    assert len(result["adjustments"]) > 0


def test_quality_priority(tmp_path):
    """Quality priority should yield fine layers (<= 0.12mm)."""
    mesh = trimesh.primitives.Box(extents=(20, 20, 20))
    mesh_path = tmp_path / "box.stl"
    mesh.export(str(mesh_path))

    result = optimize_settings(str(mesh_path), priority="quality")

    assert result["status"] == "success"
    assert result["settings"]["layer_height"] <= 0.12
    assert result["settings"]["print_speed"] <= 100
    assert isinstance(result["adjustments"], list)


def test_printer_speed_cap(tmp_path):
    """A1M printer should cap print speeds below the speed-priority default of 300."""
    mesh = trimesh.primitives.Box(extents=(20, 20, 20))
    mesh_path = tmp_path / "box.stl"
    mesh.export(str(mesh_path))

    result = optimize_settings(str(mesh_path), priority="speed", printer_model="A1M")

    assert result["status"] == "success"
    assert result["settings"]["print_speed"] < 300
    any_cap_adjustment = any("capped" in a.lower() or "cap" in a.lower() for a in result["adjustments"])
    assert any_cap_adjustment
