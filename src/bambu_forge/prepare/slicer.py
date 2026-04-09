"""Bambu Studio CLI slicer wrapper."""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path
from typing import Any


def build_slice_command(
    slicer_path: str,
    input_file: str,
    output_file: str,
    machine_settings: str | None = None,
    process_settings: str | None = None,
    filament_settings: str | None = None,
    plate_index: int = 0,
) -> list[str]:
    cmd = [slicer_path, "--slice", str(plate_index)]

    if process_settings:
        cmd += ["--load-settings", process_settings]
    if filament_settings:
        cmd += ["--load-filaments", filament_settings]
    if machine_settings:
        cmd += ["--load-machine", machine_settings]

    cmd += ["--export-3mf", output_file, input_file]
    return cmd


def mock_slice_result(input_file: str) -> dict[str, Any]:
    return {
        "success": True,
        "input_file": input_file,
        "print_time": 128,
        "filament_grams": 22.8,
        "layers": 187,
        "error": "",
    }


def run_slicer(
    slicer_path: str,
    input_file: str,
    output_file: str,
    machine_settings: str | None = None,
    process_settings: str | None = None,
    filament_settings: str | None = None,
    plate_index: int = 0,
    mock: bool = False,
    timeout: int = 300,
) -> dict[str, Any]:
    if mock:
        return mock_slice_result(input_file)

    if not Path(slicer_path).exists() and not shutil.which(slicer_path):
        return {"success": False, "error": f"Slicer not found: {slicer_path}"}

    cmd = build_slice_command(
        slicer_path=slicer_path,
        input_file=input_file,
        output_file=output_file,
        machine_settings=machine_settings,
        process_settings=process_settings,
        filament_settings=filament_settings,
        plate_index=plate_index,
    )

    try:
        result = subprocess.run(
            cmd,
            timeout=timeout,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            error = result.stderr.strip() or result.stdout.strip() or "Slicer failed"
            return {"success": False, "error": error}
        return {
            "success": True,
            "output_file": output_file,
            "stdout": result.stdout,
            "error": "",
        }
    except subprocess.TimeoutExpired:
        return {"success": False, "error": f"Slicer timeout: exceeded {timeout}s"}
    except Exception as exc:
        return {"success": False, "error": str(exc)}
