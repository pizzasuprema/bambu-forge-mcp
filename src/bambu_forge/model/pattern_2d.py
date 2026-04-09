"""Subprocess-isolated 2D pattern generation (SVG via svgwrite, DXF via ezdxf)."""

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


def generate_2d_pattern(
    code: str,
    output_format: str,
    output_path: str,
    workspace: str,
    timeout: int = 30,
) -> dict:
    """Execute user code to generate an SVG or DXF pattern in a subprocess."""
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
            return {"status": "error", "error": error}

        if not Path(output_path).exists():
            return {
                "status": "error",
                "error": "Code ran successfully but no output file was created.",
            }

        return {
            "status": "success",
            "file_path": output_path,
            "format": output_format,
            "size_bytes": Path(output_path).stat().st_size,
        }

    except subprocess.TimeoutExpired:
        return {"status": "error", "error": f"Timeout: execution exceeded {timeout}s"}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}
    finally:
        Path(tmp_file).unlink(missing_ok=True)
