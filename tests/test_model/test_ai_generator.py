import pytest

from bambu_forge.model.ai_generator import submit_generation, check_generation, _mock_jobs


@pytest.fixture(autouse=True)
def clear_mock_jobs():
    _mock_jobs.clear()
    yield
    _mock_jobs.clear()


@pytest.mark.asyncio
async def test_submit_mock():
    result = await submit_generation("a small vase", style="realistic", mock=True)

    assert result["status"] == "success"
    assert "job_id" in result
    assert result["provider"] == "meshy"
    assert result["estimated_seconds"] > 0


@pytest.mark.asyncio
async def test_check_mock_completed(tmp_path):
    submit_result = await submit_generation("a cube", mock=True)
    job_id = submit_result["job_id"]

    result = await check_generation(job_id, workspace=str(tmp_path), mock=True)

    assert result["status"] == "success"
    assert result["generation_status"] == "completed"
    assert result["progress_percent"] == 100
    assert result["triangle_count"] > 0
    assert result["file_path"].endswith(".stl")

    import os
    assert os.path.exists(result["file_path"])


@pytest.mark.asyncio
async def test_submit_no_api_key(monkeypatch):
    monkeypatch.delenv("MESHY_API_KEY", raising=False)

    result = await submit_generation("a vase", mock=False)

    assert result["status"] == "error"
    assert result["error_code"] == "API_KEY_MISSING"
