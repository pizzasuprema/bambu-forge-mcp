import numpy as np
import pytest
import trimesh

from bambu_forge.prepare.analyzer import analyze_printability


def test_analyze_simple_box(tmp_path):
    """A unit box should produce all 7 dimension scores, each 0-100, and an int overall_score."""
    mesh = trimesh.primitives.Box(extents=(20, 20, 20))
    mesh_path = tmp_path / "box.stl"
    mesh.export(str(mesh_path))

    result = analyze_printability(str(mesh_path))

    assert result["status"] == "success"
    assert isinstance(result["overall_score"], int)
    assert 0 <= result["overall_score"] <= 100

    expected_dims = [
        "overhangs",
        "thin_walls",
        "bridging",
        "bed_adhesion",
        "supports",
        "warping",
        "thermal_stress",
    ]
    for dim in expected_dims:
        assert dim in result["dimensions"], f"Missing dimension: {dim}"
        score = result["dimensions"][dim]["score"]
        assert isinstance(score, int)
        assert 0 <= score <= 100
        assert isinstance(result["dimensions"][dim]["recommendations"], list)


def test_overhang_detection(tmp_path):
    """A mesh with steep overhangs should score lower on overhangs than a flat box."""
    box = trimesh.primitives.Box(extents=(20, 20, 20))
    box_path = tmp_path / "box.stl"
    box.export(str(box_path))
    box_result = analyze_printability(str(box_path))

    cone = trimesh.creation.cone(radius=30, height=5)
    cone_path = tmp_path / "cone.stl"
    cone.export(str(cone_path))
    cone_result = analyze_printability(str(cone_path))

    assert cone_result["dimensions"]["overhangs"]["score"] < box_result["dimensions"]["overhangs"]["score"]


def test_build_volume_check(tmp_path):
    """Small box fits H2C (320x320x320); huge box does not."""
    small = trimesh.primitives.Box(extents=(10, 10, 10))
    small_path = tmp_path / "small.stl"
    small.export(str(small_path))
    small_result = analyze_printability(str(small_path), printer_model="H2C")

    assert small_result["bambu_specific"]["fits_build_volume"] is True
    for margin in small_result["bambu_specific"]["build_volume_margin"]:
        assert margin > 0

    huge = trimesh.primitives.Box(extents=(500, 500, 500))
    huge_path = tmp_path / "huge.stl"
    huge.export(str(huge_path))
    huge_result = analyze_printability(str(huge_path), printer_model="H2C")

    assert huge_result["bambu_specific"]["fits_build_volume"] is False


def test_missing_file():
    """Analyzing a nonexistent file should return status='error'."""
    result = analyze_printability("/nonexistent/model.stl")

    assert result["status"] == "error"
    assert "error" in result or "message" in result
