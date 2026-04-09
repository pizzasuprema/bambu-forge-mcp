"""Submit/poll pattern for AI text-to-3D generation (mock + real API stubs)."""

from __future__ import annotations

import os
import uuid


_mock_jobs: dict[str, dict] = {}


async def submit_generation(
    description: str,
    style: str = "realistic",
    provider: str = "meshy",
    mock: bool = False,
) -> dict:
    """Submit a text-to-3D job. Returns immediately with job_id."""
    if mock:
        job_id = f"mock_{uuid.uuid4().hex[:8]}"
        _mock_jobs[job_id] = {
            "status": "completed",
            "description": description,
            "provider": provider,
        }
        return {
            "status": "success",
            "job_id": job_id,
            "provider": provider,
            "estimated_seconds": 60,
        }

    api_key = os.environ.get(f"{provider.upper()}_API_KEY")
    if not api_key:
        return {
            "status": "error",
            "error_code": "API_KEY_MISSING",
            "message": f"{provider} API key not configured. Set {provider.upper()}_API_KEY env var.",
        }

    return {
        "status": "error",
        "error_code": "NOT_IMPLEMENTED",
        "message": f"Real {provider} API integration pending. Use mock mode for testing.",
    }


async def check_generation(
    job_id: str, workspace: str, mock: bool = False
) -> dict:
    """Check status of a generation job. On completion, saves mesh to workspace."""
    if mock:
        if job_id not in _mock_jobs:
            return {
                "status": "error",
                "error_code": "JOB_NOT_FOUND",
                "message": f"No job with ID {job_id}",
            }
        import trimesh

        mesh = trimesh.creation.box(extents=[30, 30, 30])
        output_path = os.path.join(workspace, f"{job_id}.stl")
        mesh.export(output_path)
        return {
            "status": "success",
            "generation_status": "completed",
            "progress_percent": 100,
            "file_path": output_path,
            "triangle_count": len(mesh.faces),
        }

    return {
        "status": "error",
        "error_code": "NOT_IMPLEMENTED",
        "message": "Real API polling not yet implemented.",
    }
