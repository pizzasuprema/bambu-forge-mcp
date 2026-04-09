import pytest

from bambu_forge.profiles.tools import (
    delete_profile_impl,
    get_profile_impl,
    list_profiles_impl,
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
