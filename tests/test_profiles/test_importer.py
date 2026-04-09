import json

import pytest

from bambu_forge.profiles.importer import discover_user_profiles, resolve_inheritance


def _write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data))


def test_discover_user_profiles(tmp_path):
    _write_json(
        tmp_path / "user" / "12345" / "process" / "Custom.json",
        {"name": "Custom", "layer_height": 0.2},
    )
    _write_json(
        tmp_path / "user" / "12345" / "filament" / "MyPLA.json",
        {"name": "MyPLA", "temp": 210},
    )

    profiles = discover_user_profiles(tmp_path)
    assert len(profiles) == 2

    names = {p["name"] for p in profiles}
    assert "Custom" in names
    assert "MyPLA" in names

    types = {p["_profile_type"] for p in profiles}
    assert "process" in types
    assert "filament" in types


def test_resolve_inheritance_simple():
    child = {"name": "Custom", "inherits": "Parent", "layer_height": 0.28}
    bases = {
        "Parent": {"name": "Parent", "layer_height": 0.2, "infill": 15},
    }

    resolved = resolve_inheritance(child, bases)
    assert resolved["layer_height"] == 0.28
    assert resolved["infill"] == 15


def test_resolve_inheritance_chain():
    child = {"name": "Child", "inherits": "Parent", "layer_height": 0.3}
    bases = {
        "Parent": {"name": "Parent", "inherits": "Grandparent", "infill": 20},
        "Grandparent": {"name": "Grandparent", "speed": 60, "infill": 10},
    }

    resolved = resolve_inheritance(child, bases)
    assert resolved["layer_height"] == 0.3
    assert resolved["infill"] == 20
    assert resolved["speed"] == 60


def test_resolve_inheritance_cycle_detection():
    a = {"name": "A", "inherits": "B", "val": 1}
    b = {"name": "B", "inherits": "A", "val": 2}
    bases = {"A": a, "B": b}

    with pytest.raises(ValueError, match="circular"):
        resolve_inheritance(a, bases)
