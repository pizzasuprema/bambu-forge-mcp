import pytest

from bambu_forge.model.marketplace import search_marketplace


@pytest.mark.asyncio
async def test_search_mock():
    result = await search_marketplace("Phone", mock=True)

    assert result["status"] == "success"
    assert result["source"] == "makerworld"
    assert result["count"] >= 1

    names = [r["name"] for r in result["results"]]
    assert any("Phone" in n for n in names)


@pytest.mark.asyncio
async def test_search_no_match():
    result = await search_marketplace("xyznonexistent", mock=True)

    assert result["status"] == "success"
    assert result["count"] == 0
    assert result["results"] == []
