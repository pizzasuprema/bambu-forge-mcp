from __future__ import annotations

import json
from pathlib import Path
from typing import Any

_META_KEYS = frozenset({"name", "inherits", "from", "version", "setting_id", "type"})
_MAX_DEPTH = 10
_PROFILE_DIRS = ("process", "filament", "machine")


def discover_user_profiles(studio_path: str | Path) -> list[dict[str, Any]]:
    """Walk user/{uid}/(process|filament|machine)/*.json and return parsed profiles."""
    studio_path = Path(studio_path)
    user_dir = studio_path / "user"
    if not user_dir.is_dir():
        return []

    profiles: list[dict[str, Any]] = []
    for uid_dir in user_dir.iterdir():
        if not uid_dir.is_dir():
            continue
        for profile_type in _PROFILE_DIRS:
            type_dir = uid_dir / profile_type
            if not type_dir.is_dir():
                continue
            for json_file in type_dir.glob("*.json"):
                try:
                    data = json.loads(json_file.read_text(encoding="utf-8"))
                except (json.JSONDecodeError, OSError):
                    continue
                if not isinstance(data, dict):
                    continue
                if "name" not in data:
                    data["name"] = json_file.stem
                data["_profile_type"] = profile_type
                data["_source_path"] = str(json_file)
                profiles.append(data)

    return profiles


def resolve_inheritance(
    profile: dict[str, Any],
    base_profiles: dict[str, dict[str, Any]],
    _visited: set[str] | None = None,
    _depth: int = 0,
) -> dict[str, Any]:
    """Recursively resolve a profile's inheritance chain.

    Raises ValueError on circular inheritance or depth > MAX_DEPTH.
    """
    name = profile.get("name", "<unnamed>")

    if _visited is None:
        _visited = set()

    if name in _visited:
        raise ValueError(f"circular inheritance detected: {name}")
    _visited.add(name)

    if _depth > _MAX_DEPTH:
        raise ValueError(f"inheritance depth exceeded {_MAX_DEPTH} for {name}")

    parent_name = profile.get("inherits")
    if parent_name and parent_name in base_profiles:
        parent = base_profiles[parent_name]
        resolved_parent = resolve_inheritance(
            parent, base_profiles, _visited, _depth + 1
        )
    else:
        resolved_parent = {}

    result = dict(resolved_parent)
    for key, value in profile.items():
        if key not in _META_KEYS:
            result[key] = value

    return result
