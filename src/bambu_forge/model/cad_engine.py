"""CadQuery subprocess executor with timeout, env stripping, and isolation."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

_STRIPPED_ENV_KEYS = frozenset({
    "BAMBU_ACCESS_CODE",
    "MESHY_API_KEY",
    "TRIPO3D_API_KEY",
})


def execute_cadquery(
    code: str,
    output_path: str,
    workspace: str,
    timeout: int = 60,
) -> dict:
    safe_output = output_path.replace("\\", "\\\\").replace('"', '\\"')
    full_code = f'OUTPUT_PATH = "{safe_output}"\n{code}'

    env = {k: v for k, v in os.environ.items() if k not in _STRIPPED_ENV_KEYS}

    tmp_fd, tmp_file = tempfile.mkstemp(suffix=".py", dir=workspace)
    try:
        with os.fdopen(tmp_fd, "w") as f:
            f.write(full_code)

        result = subprocess.run(
            [sys.executable, tmp_file],
            cwd=workspace,
            timeout=timeout,
            capture_output=True,
            text=True,
            env=env,
        )

        if result.returncode != 0:
            error = result.stderr.strip() or result.stdout.strip() or "Unknown error"
            return {"success": False, "error": error}

        return {"success": True, "error": ""}

    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Timeout: execution exceeded {timeout}s"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}
    finally:
        Path(tmp_file).unlink(missing_ok=True)
