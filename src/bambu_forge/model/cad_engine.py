"""CadQuery subprocess executor with timeout, env stripping, and isolation."""

from __future__ import annotations

import os
import subprocess
import sys
import tempfile
from pathlib import Path

_ALLOWED_ENV_KEYS = frozenset({
    "PATH", "HOME", "LANG", "TMPDIR", "VIRTUAL_ENV",
    "PYTHONPATH", "LC_ALL", "USER",
})


def execute_cadquery(
    code: str,
    output_path: str,
    workspace: str,
    timeout: int = 60,
) -> dict:
    full_code = f'import os\nOUTPUT_PATH = os.environ["OUTPUT_PATH"]\n{code}'

    env = {k: v for k, v in os.environ.items() if k in _ALLOWED_ENV_KEYS}
    env["OUTPUT_PATH"] = output_path

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
            stdin=subprocess.DEVNULL,
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
