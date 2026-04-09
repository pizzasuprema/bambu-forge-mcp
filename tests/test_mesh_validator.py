"""Tests for STL mesh validation (trimesh-based)."""

import trimesh

from bambu_forge.mesh_validator import validate_mesh


def test_valid_mesh(tmp_path):
    mesh = trimesh.creation.box(extents=[10, 20, 30])
    stl_path = tmp_path / "box.stl"
    mesh.export(str(stl_path))
    result = validate_mesh(str(stl_path))
    assert result.valid is True
    assert result.triangle_count > 0
    assert result.bounding_box is not None
    assert len(result.warnings) == 0


def test_empty_file(tmp_path):
    stl_path = tmp_path / "empty.stl"
    stl_path.write_bytes(b"")
    result = validate_mesh(str(stl_path))
    assert result.valid is False
    assert any(
        "fatal" in e.lower() or "parse" in e.lower() for e in result.errors
    )


def test_nonexistent_file():
    result = validate_mesh("/nonexistent/mesh.stl")
    assert result.valid is False
