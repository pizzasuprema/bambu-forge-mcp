import pytest

from bambu_forge.profiles.store import ProfileStore


@pytest.fixture
def store(tmp_path):
    db = tmp_path / "profiles.db"
    s = ProfileStore(db_path=db)
    yield s
    s.close()


def test_save_and_get_profile(store):
    store.save_profile(
        name="MyProfile",
        base_profile="0.20mm Standard",
        overrides={"layer_height": 0.28, "infill": 30},
        profile_type="process",
    )
    p = store.get_profile("MyProfile")
    assert p is not None
    assert p["name"] == "MyProfile"
    assert p["inherits"] == "0.20mm Standard"
    assert p["overrides"]["layer_height"] == 0.28
    assert p["overrides"]["infill"] == 30
    assert p["profile_type"] == "process"
    assert "created_at" in p


def test_list_profiles(store):
    store.save_profile("ProcessOne", "base", {}, "process")
    store.save_profile("FilamentOne", "base", {}, "filament")

    all_profiles = store.list_profiles()
    assert len(all_profiles) == 2

    process_only = store.list_profiles(profile_type="process")
    assert len(process_only) == 1
    assert process_only[0]["name"] == "ProcessOne"


def test_delete_profile(store):
    store.save_profile("ToDelete", "base", {}, "process")
    assert store.get_profile("ToDelete") is not None

    result = store.delete_profile("ToDelete")
    assert result is True
    assert store.get_profile("ToDelete") is None


def test_delete_nonexistent_returns_false(store):
    result = store.delete_profile("Nope")
    assert result is False


def test_save_filament(store):
    store.save_filament(
        name="MyPLA",
        properties={"temp": 210, "bed_temp": 60, "brand": "eSUN"},
    )
    filaments = store.list_filaments()
    assert len(filaments) == 1
    assert filaments[0]["name"] == "MyPLA"
    assert filaments[0]["properties"]["temp"] == 210
