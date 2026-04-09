import pytest
import trimesh

from bambu_forge.model.stl_ops import modify_model, combine_models


@pytest.fixture
def box_stl(tmp_path):
    mesh = trimesh.creation.box(extents=[10, 20, 30])
    path = str(tmp_path / "box.stl")
    mesh.export(path)
    return path


def test_scale_model(box_stl, tmp_path):
    output = str(tmp_path / "scaled.stl")
    result = modify_model(box_stl, [{"type": "scale", "factor": 2}], output)

    assert result["status"] == "success"
    assert "scale" in result["operations_applied"]

    scaled = trimesh.load(output, force="mesh")
    extents = scaled.bounding_box.extents
    assert pytest.approx(extents[0], abs=0.5) == 20
    assert pytest.approx(extents[1], abs=0.5) == 40
    assert pytest.approx(extents[2], abs=0.5) == 60


def test_rotate_model(box_stl, tmp_path):
    output = str(tmp_path / "rotated.stl")
    result = modify_model(box_stl, [{"type": "rotate", "axis": "z", "degrees": 90}], output)

    assert result["status"] == "success"

    rotated = trimesh.load(output, force="mesh")
    extents = sorted(rotated.bounding_box.extents)
    # Original 10x20x30 rotated 90 on Z -> 20x10x30 (x/y swap)
    assert pytest.approx(extents[0], abs=0.5) == 10
    assert pytest.approx(extents[1], abs=0.5) == 20
    assert pytest.approx(extents[2], abs=0.5) == 30


def test_combine_union(tmp_path):
    box_a = trimesh.creation.box(extents=[10, 10, 10])
    box_b = trimesh.creation.box(extents=[10, 10, 10])
    box_b.apply_translation([5, 0, 0])

    path_a = str(tmp_path / "a.stl")
    path_b = str(tmp_path / "b.stl")
    box_a.export(path_a)
    box_b.export(path_b)

    output = str(tmp_path / "union.stl")
    result = combine_models(path_a, path_b, "union", output)

    assert result["status"] == "success"
    assert result["triangle_count"] > 0

    import os
    assert os.path.exists(output)


def test_modify_missing_file(tmp_path):
    output = str(tmp_path / "out.stl")
    result = modify_model("/nonexistent/model.stl", [{"type": "scale", "factor": 2}], output)

    assert result["status"] == "error"
    assert result["error_code"] == "MESH_LOAD_FAILED"
