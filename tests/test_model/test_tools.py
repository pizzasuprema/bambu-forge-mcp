import pytest

from bambu_forge.model.tools import generate_model_impl, list_designs_impl


CADQUERY_BOX = """\
import cadquery as cq

result = cq.Workplane("XY").box(10, 20, 5)
cq.exporters.export(result, OUTPUT_PATH)
"""


@pytest.mark.asyncio
async def test_generate_model_creates_file(tmp_path):
    db = tmp_path / "dna.db"
    result = await generate_model_impl(
        code=CADQUERY_BOX,
        output_name="box",
        workspace=str(tmp_path),
        db_path=str(db),
        timeout=120,
    )

    assert result["status"] == "success"
    assert result["triangle_count"] > 0
    assert result["valid"] is True
    assert "design_id" in result


@pytest.mark.asyncio
async def test_list_designs_empty(tmp_path):
    db = tmp_path / "dna.db"
    result = await list_designs_impl(query=None, db_path=str(db))

    assert result["status"] == "success"
    assert result["data"] == []
