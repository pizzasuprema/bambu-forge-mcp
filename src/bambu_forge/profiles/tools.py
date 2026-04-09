from __future__ import annotations

from pathlib import Path
from typing import Any

from bambu_forge.profiles.store import ProfileStore


def _default_db_path(get_config) -> Path:
    cfg = get_config()
    data_dir = Path(cfg.data_dir) if hasattr(cfg, "data_dir") and cfg.data_dir else Path.home() / ".bambu-forge"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "profiles.db"


async def save_profile_impl(
    name: str,
    base_profile: str | None = None,
    overrides: dict[str, Any] | None = None,
    profile_type: str = "process",
    db_path: str | Path | None = None,
) -> dict[str, Any]:
    store = ProfileStore(db_path=db_path or "profiles.db")
    try:
        store.save_profile(name, base_profile, overrides, profile_type)
        return {"status": "success", "message": f"Profile '{name}' saved"}
    finally:
        store.close()


async def get_profile_impl(
    name: str,
    db_path: str | Path | None = None,
) -> dict[str, Any]:
    store = ProfileStore(db_path=db_path or "profiles.db")
    try:
        profile = store.get_profile(name)
        if profile is None:
            return {
                "status": "error",
                "error_code": "PROFILE_NOT_FOUND",
                "message": f"Profile '{name}' not found",
            }
        return {"status": "success", "profile": profile}
    finally:
        store.close()


async def list_profiles_impl(
    profile_type: str | None = None,
    db_path: str | Path | None = None,
) -> dict[str, Any]:
    store = ProfileStore(db_path=db_path or "profiles.db")
    try:
        profiles = store.list_profiles(profile_type=profile_type)
        return {"status": "success", "profiles": profiles, "count": len(profiles)}
    finally:
        store.close()


async def delete_profile_impl(
    name: str,
    db_path: str | Path | None = None,
) -> dict[str, Any]:
    store = ProfileStore(db_path=db_path or "profiles.db")
    try:
        deleted = store.delete_profile(name)
        return {"status": "success", "deleted": deleted}
    finally:
        store.close()


async def list_filaments_impl(
    filter_text: str | None = None,
    db_path: str | Path | None = None,
) -> dict[str, Any]:
    store = ProfileStore(db_path=db_path or "profiles.db")
    try:
        filaments = store.list_filaments(filter_text=filter_text)
        return {"status": "success", "filaments": filaments, "count": len(filaments)}
    finally:
        store.close()


async def recommend_profile_impl(
    material: str | None = None,
    model_type: str | None = None,
) -> dict[str, Any]:
    return {
        "status": "success",
        "message": "Profile recommendation engine coming in Phase 3",
        "material": material,
        "model_type": model_type,
    }


async def import_studio_config_impl(
    studio_path: str | None = None,
) -> dict[str, Any]:
    return {
        "status": "success",
        "message": "Import requires Bambu Studio installation path. Auto-detection coming in Phase 3.",
        "studio_path": studio_path,
    }


def register_profile_tools(mcp, get_config):
    @mcp.tool()
    async def list_profiles(profile_type: str | None = None) -> dict[str, Any]:
        """List saved print profiles, optionally filtered by type (process, filament, machine)."""
        db = _default_db_path(get_config)
        return await list_profiles_impl(profile_type=profile_type, db_path=db)

    @mcp.tool()
    async def get_profile(name: str) -> dict[str, Any]:
        """Get a specific profile by name with all settings and overrides."""
        db = _default_db_path(get_config)
        return await get_profile_impl(name=name, db_path=db)

    @mcp.tool()
    async def save_profile(
        name: str,
        base_profile: str | None = None,
        overrides: str = "{}",
        profile_type: str = "process",
    ) -> dict[str, Any]:
        """Save a print profile. Overrides is a JSON string of settings that differ from the base profile."""
        import json

        parsed = json.loads(overrides)
        db = _default_db_path(get_config)
        return await save_profile_impl(
            name=name, base_profile=base_profile, overrides=parsed,
            profile_type=profile_type, db_path=db,
        )

    @mcp.tool()
    async def delete_profile(name: str) -> dict[str, Any]:
        """Delete a saved profile by name."""
        db = _default_db_path(get_config)
        return await delete_profile_impl(name=name, db_path=db)

    @mcp.tool()
    async def recommend_profile(
        material: str | None = None,
        model_type: str | None = None,
    ) -> dict[str, Any]:
        """Recommend optimal print profile based on material and model type (Phase 3 stub)."""
        return await recommend_profile_impl(material=material, model_type=model_type)

    @mcp.tool()
    async def list_filaments(filter_text: str | None = None) -> dict[str, Any]:
        """List known filament profiles, optionally filtered by name substring."""
        db = _default_db_path(get_config)
        return await list_filaments_impl(filter_text=filter_text, db_path=db)

    @mcp.tool()
    async def import_studio_config(studio_path: str | None = None) -> dict[str, Any]:
        """Import profiles from a local Bambu Studio installation (Phase 3 stub)."""
        return await import_studio_config_impl(studio_path=studio_path)
