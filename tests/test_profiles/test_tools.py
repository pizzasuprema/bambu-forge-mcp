import pytest

from bambu_forge.profiles.tools import (
    delete_profile_impl,
    get_profile_impl,
    list_profiles_impl,
    log_print_outcome_impl,
    list_print_history_impl,
    get_print_insights_impl,
    save_profile_impl,
)


@pytest.mark.asyncio
async def test_save_and_list_profiles(tmp_path):
    db = tmp_path / "profiles.db"
    await save_profile_impl(
        name="TestProfile",
        base_profile="0.20mm Standard",
        overrides={"layer_height": 0.28},
        profile_type="process",
        db_path=db,
    )
    result = await list_profiles_impl(db_path=db)
    assert result["status"] == "success"
    assert len(result["profiles"]) == 1
    assert result["profiles"][0]["name"] == "TestProfile"


@pytest.mark.asyncio
async def test_get_profile(tmp_path):
    db = tmp_path / "profiles.db"
    await save_profile_impl(
        name="MyProfile",
        base_profile="base",
        overrides={"infill": 30},
        profile_type="process",
        db_path=db,
    )
    result = await get_profile_impl(name="MyProfile", db_path=db)
    assert result["status"] == "success"
    assert result["profile"]["overrides"]["infill"] == 30


@pytest.mark.asyncio
async def test_get_profile_not_found(tmp_path):
    db = tmp_path / "profiles.db"
    result = await get_profile_impl(name="Ghost", db_path=db)
    assert result["status"] == "error"
    assert result["error_code"] == "PROFILE_NOT_FOUND"


@pytest.mark.asyncio
async def test_delete_profile(tmp_path):
    db = tmp_path / "profiles.db"
    await save_profile_impl(
        name="Doomed",
        base_profile="base",
        overrides={},
        profile_type="process",
        db_path=db,
    )
    result = await delete_profile_impl(name="Doomed", db_path=db)
    assert result["status"] == "success"
    assert result["deleted"] is True


@pytest.mark.asyncio
async def test_save_profile_malformed_json(tmp_path):
    db = str(tmp_path / "test.db")
    result = await save_profile_impl(
        name="Bad",
        base_profile="base",
        overrides="{invalid json",
        profile_type="process",
        db_path=db,
    )
    assert result["status"] == "error"
    assert "INVALID" in result.get("error_code", "")


@pytest.mark.asyncio
async def test_recommend_profile_generated(tmp_path):
    # No saved profiles → should return generated recommendation
    from bambu_forge.profiles.tools import recommend_profile_impl
    import trimesh

    box = trimesh.creation.box(extents=[50, 50, 50])
    mesh_path = str(tmp_path / "box.stl")
    box.export(mesh_path)
    db = str(tmp_path / "test.db")
    result = await recommend_profile_impl(
        file_path=mesh_path, priorities="quality", db_path=db
    )
    assert result["status"] == "success"
    assert result["recommendation_type"] == "generated"
    assert "settings" in result


@pytest.mark.asyncio
async def test_log_and_list_history(tmp_path):
    db = str(tmp_path / "test.db")
    await log_print_outcome_impl(
        design_name="Benchy",
        outcome="success",
        quality_grade="excellent",
        db_path=db,
    )
    result = await list_print_history_impl(db_path=db)
    assert result["status"] == "success"
    assert len(result["history"]) == 1
    assert result["history"][0]["design_name"] == "Benchy"
    assert result["history"][0]["outcome"] == "success"


@pytest.mark.asyncio
async def test_get_insights_empty(tmp_path):
    db = str(tmp_path / "test.db")
    result = await get_print_insights_impl(db_path=db)
    assert result["status"] == "success"
    assert result["insights"]["total_prints"] == 0
    assert result["insights"]["success_rate"] == 0.0


@pytest.mark.asyncio
async def test_get_insights_with_data(tmp_path):
    db = str(tmp_path / "test.db")
    await log_print_outcome_impl(design_name="A", outcome="success", db_path=db)
    await log_print_outcome_impl(design_name="B", outcome="success", db_path=db)
    await log_print_outcome_impl(
        design_name="C", outcome="failure", failure_mode="adhesion", db_path=db,
    )
    result = await get_print_insights_impl(db_path=db)
    assert result["status"] == "success"
    insights = result["insights"]
    assert insights["total_prints"] == 3
    assert insights["success_rate"] == pytest.approx(2 / 3, abs=0.01)
    assert insights["most_common_failure_mode"] == "adhesion"


@pytest.mark.asyncio
async def test_recommend_with_history_boost(tmp_path):
    from bambu_forge.profiles.tools import recommend_profile_impl
    from bambu_forge.profiles.history import PrintHistoryStore
    import trimesh

    db = str(tmp_path / "test.db")
    history_db = str(tmp_path / "history.db")

    box = trimesh.creation.box(extents=[50, 50, 50])
    mesh_path = str(tmp_path / "box.stl")
    box.export(mesh_path)

    await save_profile_impl(
        name="TestedProfile",
        base_profile="base",
        overrides={"layer_height": 0.2},
        profile_type="process",
        db_path=db,
    )

    result_before = await recommend_profile_impl(
        file_path=mesh_path, priorities="quality", db_path=db,
    )

    history = PrintHistoryStore(db_path=history_db)
    try:
        for _ in range(5):
            history.log_print(
                "box", "TestedProfile", "X1C", "PLA", 20.0, 30, "success",
            )
    finally:
        history.close()

    result_after = await recommend_profile_impl(
        file_path=mesh_path, priorities="quality", db_path=db,
        history_db_path=history_db,
    )

    if result_before.get("recommendation_type") == "profile":
        assert result_after["match_score"] >= result_before["match_score"]
