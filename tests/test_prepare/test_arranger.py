import trimesh

from bambu_forge.prepare.arranger import arrange_plate


def test_two_small_models_fit(tmp_path):
    """Two 50x50mm boxes should both fit on a 256x256 plate."""
    paths = []
    for name in ("a.stl", "b.stl"):
        mesh = trimesh.primitives.Box(extents=(50, 50, 10))
        p = tmp_path / name
        mesh.export(str(p))
        paths.append(str(p))

    result = arrange_plate(paths, strategy="compact", build_volume=(256, 256, 256))

    assert result["status"] == "success"
    assert len(result["placements"]) == 2
    assert all(p["fits"] for p in result["placements"])
    assert result["overflow"] == []
    assert 0 < result["plate_utilization"] <= 1.0


def test_oversized_model(tmp_path):
    """A 500x500mm box should end up in overflow on a 256x256 plate."""
    mesh = trimesh.primitives.Box(extents=(500, 500, 10))
    p = tmp_path / "huge.stl"
    mesh.export(str(p))

    result = arrange_plate([str(p)], strategy="compact", build_volume=(256, 256, 256))

    assert result["status"] == "success"
    assert len(result["overflow"]) == 1
    assert result["placements"] == [] or not result["placements"][0]["fits"]


def test_strategies_differ(tmp_path):
    """Compact vs accessible strategies should produce different gaps/positions."""
    paths = []
    for name in ("x.stl", "y.stl"):
        mesh = trimesh.primitives.Box(extents=(50, 50, 10))
        p = tmp_path / name
        mesh.export(str(p))
        paths.append(str(p))

    compact = arrange_plate(paths, strategy="compact", build_volume=(256, 256, 256))
    accessible = arrange_plate(paths, strategy="accessible", build_volume=(256, 256, 256))

    assert compact["status"] == "success"
    assert accessible["status"] == "success"

    compact_positions = [tuple(p["position"]) for p in compact["placements"]]
    accessible_positions = [tuple(p["position"]) for p in accessible["placements"]]
    assert compact_positions != accessible_positions
