import pytest

from bambu_forge.profiles.store import ProfileStore


@pytest.fixture
def store(tmp_path):
    s = ProfileStore(db_path=tmp_path / "profiles.db")
    yield s
    s.close()


def test_add_and_list_spools(store):
    id1 = store.add_spool("eSUN PLA+", "PLA", "White", 1000.0, 20.0)
    id2 = store.add_spool("Polymaker PETG", "PETG", "Black", 1000.0, 25.0)

    all_spools = store.list_spools()
    assert len(all_spools) == 2

    pla_only = store.list_spools(filament_type="PLA")
    assert len(pla_only) == 1
    assert pla_only[0]["filament_name"] == "eSUN PLA+"
    assert pla_only[0]["color"] == "White"
    assert pla_only[0]["weight_remaining_g"] == 1000.0
    assert pla_only[0]["price_per_kg"] == 20.0


def test_use_filament(store):
    spool_id = store.add_spool("eSUN PLA+", "PLA", "White", 1000.0, 20.0)

    updated = store.use_filament(spool_id, 200.0)
    assert updated["weight_remaining_g"] == pytest.approx(800.0)

    spool = store.get_spool(spool_id)
    assert spool["weight_remaining_g"] == pytest.approx(800.0)


def test_use_filament_insufficient(store):
    spool_id = store.add_spool("eSUN PLA+", "PLA", "White", 1000.0, 20.0)
    store.use_filament(spool_id, 900.0)

    result = store.use_filament(spool_id, 200.0)
    assert "warning" in result
