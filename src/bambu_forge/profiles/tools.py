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
    overrides: dict[str, Any] | str | None = None,
    profile_type: str = "process",
    db_path: str | Path | None = None,
) -> dict[str, Any]:
    import json
    if isinstance(overrides, str):
        try:
            overrides = json.loads(overrides)
        except (json.JSONDecodeError, TypeError):
            return {
                "status": "error",
                "error_code": "INVALID_JSON",
                "message": f"overrides is not valid JSON: {overrides!r}",
            }
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
    file_path: str,
    priorities: str = "quality",
    db_path: str | Path | None = None,
    printer_model: str | None = None,
) -> dict[str, Any]:
    from bambu_forge.prepare.optimizer import optimize_settings

    optimized = optimize_settings(file_path, priorities, printer_model)
    if optimized["status"] != "success":
        return optimized

    ideal = optimized["settings"]

    store = ProfileStore(db_path=db_path or "profiles.db")
    try:
        profiles = store.list_profiles(profile_type="process")
        if not profiles:
            return {
                "status": "success",
                "recommendation_type": "generated",
                "settings": ideal,
                "adjustments": optimized.get("adjustments", []),
                "message": "No saved profiles found. Using optimized settings.",
            }

        best_match = None
        best_score = -1
        max_possible = len(ideal)
        for p in profiles:
            overrides = p.get("overrides")
            if not overrides:
                continue
            score = sum(1 for k, v in ideal.items() if overrides.get(k) == v)
            if score > best_score:
                best_score = score
                best_match = p

        if best_match and best_score > 0:
            normalized_score = round(best_score / max_possible, 4) if max_possible else 0.0
            return {
                "status": "success",
                "recommendation_type": "profile",
                "profile_name": best_match["name"],
                "match_score": normalized_score,
                "max_possible_score": max_possible,
                "settings": ideal,
                "message": (
                    f"Recommended profile: {best_match['name']} "
                    f"({best_score}/{max_possible} matching settings)"
                ),
            }

        return {
            "status": "success",
            "recommendation_type": "generated",
            "settings": ideal,
            "adjustments": optimized.get("adjustments", []),
            "message": "No matching profiles. Using optimized settings.",
        }
    finally:
        store.close()


def _default_history_db_path(get_config) -> Path:
    cfg = get_config()
    data_dir = Path(cfg.data_dir) if hasattr(cfg, "data_dir") and cfg.data_dir else Path.home() / ".bambu-forge"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir / "history.db"


async def log_print_outcome_impl(
    design_name: str,
    outcome: str,
    quality_grade: str | None = None,
    failure_mode: str | None = None,
    notes: str | None = None,
    profile_name: str | None = None,
    printer_model: str | None = None,
    filament_type: str | None = None,
    filament_grams: float = 0.0,
    print_time_minutes: int = 0,
    settings: dict[str, Any] | None = None,
    db_path: str | Path | None = None,
) -> dict[str, Any]:
    from bambu_forge.profiles.history import PrintHistoryStore

    store = PrintHistoryStore(db_path=db_path or "history.db")
    try:
        row_id = store.log_print(
            design_name=design_name,
            profile_name=profile_name or "",
            printer_model=printer_model or "",
            filament_type=filament_type or "",
            filament_grams=filament_grams,
            print_time_minutes=print_time_minutes,
            outcome=outcome,
            quality_grade=quality_grade,
            failure_mode=failure_mode,
            settings=settings,
            notes=notes,
        )
        return {"status": "success", "id": row_id, "message": f"Print outcome logged: {outcome}"}
    finally:
        store.close()


async def list_print_history_impl(
    limit: int = 20,
    outcome: str | None = None,
    db_path: str | Path | None = None,
) -> dict[str, Any]:
    from bambu_forge.profiles.history import PrintHistoryStore

    store = PrintHistoryStore(db_path=db_path or "history.db")
    try:
        entries = store.list_history(limit=limit, outcome=outcome)
        return {"status": "success", "history": entries, "count": len(entries)}
    finally:
        store.close()


async def get_print_insights_impl(
    printer_model: str | None = None,
    db_path: str | Path | None = None,
) -> dict[str, Any]:
    from bambu_forge.profiles.history import PrintHistoryStore

    store = PrintHistoryStore(db_path=db_path or "history.db")
    try:
        insights = store.get_insights(printer_model=printer_model)
        return {"status": "success", "insights": insights}
    finally:
        store.close()


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

        try:
            parsed = json.loads(overrides)
        except (json.JSONDecodeError, TypeError):
            return {
                "status": "error",
                "error_code": "INVALID_JSON",
                "message": f"overrides is not valid JSON: {overrides!r}",
            }
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
        file_path: str,
        priorities: str = "quality",
        printer_model: str | None = None,
    ) -> dict[str, Any]:
        """Recommend a saved process profile or geometry-optimized settings for a mesh file."""
        cfg = get_config()
        if printer_model is None:
            printer_model = cfg.printer_model
        db = _default_db_path(get_config)
        return await recommend_profile_impl(
            file_path=file_path,
            priorities=priorities,
            db_path=db,
            printer_model=printer_model,
        )

    @mcp.tool()
    async def list_filaments(filter_text: str | None = None) -> dict[str, Any]:
        """List known filament profiles, optionally filtered by name substring."""
        db = _default_db_path(get_config)
        return await list_filaments_impl(filter_text=filter_text, db_path=db)

    @mcp.tool()
    async def import_studio_config(studio_path: str | None = None) -> dict[str, Any]:
        """Import profiles from a local Bambu Studio installation (Phase 3 stub)."""
        return await import_studio_config_impl(studio_path=studio_path)

    @mcp.tool()
    async def log_print_outcome(
        design_name: str,
        outcome: str,
        quality_grade: str | None = None,
        failure_mode: str | None = None,
        notes: str | None = None,
    ) -> dict[str, Any]:
        """Log the outcome of a completed print: success, failure, or cancelled."""
        db = _default_history_db_path(get_config)
        return await log_print_outcome_impl(
            design_name=design_name,
            outcome=outcome,
            quality_grade=quality_grade,
            failure_mode=failure_mode,
            notes=notes,
            db_path=db,
        )

    @mcp.tool()
    async def list_print_history(
        limit: int = 20,
        outcome: str | None = None,
    ) -> dict[str, Any]:
        """List recent print history, optionally filtered by outcome (success/failure/cancelled)."""
        db = _default_history_db_path(get_config)
        return await list_print_history_impl(limit=limit, outcome=outcome, db_path=db)

    @mcp.tool()
    async def get_print_insights() -> dict[str, Any]:
        """Get print insights: total prints, success rate, avg time, filament usage, common failures."""
        db = _default_history_db_path(get_config)
        return await get_print_insights_impl(db_path=db)
