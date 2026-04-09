import pytest

from bambu_forge.model.design_dna import DesignDnaStore


@pytest.fixture
def dna_store(tmp_path):
    db = tmp_path / "design_dna.db"
    store = DesignDnaStore(db_path=db)
    yield store
    store.close()


def test_save_and_get_design(dna_store):
    design_id = dna_store.save(
        name="phone_stand",
        source_type="cadquery",
        source_code='result = cq.Workplane("XY").box(50, 80, 3)',
        mesh_path="/tmp/phone_stand.stl",
        bbox=[[0, 0, 0], [50, 80, 3]],
        volume=12000.0,
        triangle_count=12,
    )
    assert isinstance(design_id, int)

    design = dna_store.get(design_id)
    assert design is not None
    assert design["name"] == "phone_stand"
    assert design["source_type"] == "cadquery"
    assert design["source_code"] == 'result = cq.Workplane("XY").box(50, 80, 3)'
    assert design["mesh_path"] == "/tmp/phone_stand.stl"
    assert design["bbox"] == [[0, 0, 0], [50, 80, 3]]
    assert design["volume"] == 12000.0
    assert design["triangle_count"] == 12
    assert design["parent_id"] is None
    assert "created_at" in design


def test_list_designs(dna_store):
    dna_store.save("design_a", "cadquery", "code_a", "/a.stl", [], 1.0, 10)
    dna_store.save("design_b", "cadquery", "code_b", "/b.stl", [], 2.0, 20)

    designs = dna_store.list_designs()
    assert len(designs) == 2


def test_search_designs(dna_store):
    dna_store.save("phone_stand", "cadquery", "phone code", "/a.stl", [], 1.0, 10)
    dna_store.save("bracket", "cadquery", "bracket code", "/b.stl", [], 2.0, 20)

    results = dna_store.list_designs(query="phone")
    assert len(results) == 1
    assert results[0]["name"] == "phone_stand"


def test_parent_child_chain(dna_store):
    parent_id = dna_store.save("parent", "cadquery", "v1", "/p.stl", [], 1.0, 10)
    child_id = dna_store.save(
        "child", "cadquery", "v2", "/c.stl", [], 1.5, 14, parent_id=parent_id,
    )

    child = dna_store.get(child_id)
    assert child is not None
    assert child["parent_id"] == parent_id
