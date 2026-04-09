"""Bambu Studio CLI slicer wrapper."""

from __future__ import annotations

import re
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


def mock_slice_result(input_file: str, output_file: str | None = None) -> dict[str, Any]:
    if output_file is None:
        output_file = input_file.replace(".stl", "_sliced.3mf").replace(".3mf", "_sliced.3mf")
    return {
        "success": True,
        "input_file": input_file,
        "output_file": output_file,
        "print_time": 128,
        "filament_grams": 22.8,
        "layers": 187,
        "error": "",
    }


def _parse_slicer_output(output: str) -> dict[str, Any]:
    """Best-effort extraction of metrics from Bambu Studio CLI output."""
    metrics: dict[str, Any] = {}

    time_match = re.search(r"total\s+estimated\s+time[:\s]*(\d+)", output, re.IGNORECASE)
    if time_match:
        metrics["print_time"] = int(time_match.group(1))

    filament_match = re.search(r"filament\s+used[:\s]*([\d.]+)\s*g", output, re.IGNORECASE)
    if filament_match:
        metrics["filament_grams"] = float(filament_match.group(1))

    layer_match = re.search(r"total\s+layers?[:\s]*(\d+)", output, re.IGNORECASE)
    if layer_match:
        metrics["layers"] = int(layer_match.group(1))

    return metrics


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
        return mock_slice_result(input_file, output_file)

    if not Path(slicer_path).exists() and not shutil.which(slicer_path):
        return {
            "success": False,
            "input_file": input_file,
            "print_time": None,
            "filament_grams": None,
            "layers": None,
            "error": f"Slicer not found: {slicer_path}",
            "output_file": output_file,
        }

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
            stdin=subprocess.DEVNULL,
        )
        if result.returncode != 0:
            error = result.stderr.strip() or result.stdout.strip() or "Slicer failed"
            return {
                "success": False,
                "input_file": input_file,
                "print_time": None,
                "filament_grams": None,
                "layers": None,
                "error": error,
                "output_file": output_file,
            }

        metrics = _parse_slicer_output(result.stdout + "\n" + result.stderr)
        return {
            "success": True,
            "input_file": input_file,
            "print_time": metrics.get("print_time"),
            "filament_grams": metrics.get("filament_grams"),
            "layers": metrics.get("layers"),
            "error": "",
            "output_file": output_file,
        }
    except subprocess.TimeoutExpired:
        return {
            "success": False,
            "input_file": input_file,
            "print_time": None,
            "filament_grams": None,
            "layers": None,
            "error": f"Slicer timeout: exceeded {timeout}s",
            "output_file": output_file,
        }
    except Exception as exc:
        return {
            "success": False,
            "input_file": input_file,
            "print_time": None,
            "filament_grams": None,
            "layers": None,
            "error": str(exc),
            "output_file": output_file,
        }
