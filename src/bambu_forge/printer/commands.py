from __future__ import annotations

import json
import uuid
from typing import Any

_LED_TARGET_MAP = {"chamber": "chamber_light", "bed": "work_light"}


def _seq_id() -> str:
    return uuid.uuid4().hex[:8]


def _print_cmd(command: str, **kwargs: Any) -> dict[str, Any]:
    body: dict[str, Any] = {"command": command, "sequence_id": _seq_id()}
    body.update(kwargs)
    return {"print": body}


def _system_cmd(command: str, **kwargs: Any) -> dict[str, Any]:
    body: dict[str, Any] = {"command": command, "sequence_id": _seq_id()}
    body.update(kwargs)
    return {"system": body}


def build_pause() -> dict[str, Any]:
    return _print_cmd("pause")


def build_resume() -> dict[str, Any]:
    return _print_cmd("resume")


def build_stop() -> dict[str, Any]:
    return _print_cmd("stop")


def build_speed(profile: str) -> dict[str, Any]:
    return _print_cmd("print_speed", param=profile)


def build_gcode(line: str) -> dict[str, Any]:
    return _print_cmd("gcode_line", param=line + "\n")


def build_led(target: str, on: bool) -> dict[str, Any]:
    led = _LED_TARGET_MAP[target]
    return _system_cmd("ledctrl", led=led, on=on)


def build_temp(target: str, temp_c: float | int) -> dict[str, Any]:
    if target == "nozzle":
        return build_gcode(f"M104 S{int(temp_c)}")
    if target == "bed":
        return build_gcode(f"M140 S{int(temp_c)}")
    if target == "chamber":
        return _print_cmd("set_chamber_temp", param=str(int(temp_c)))
    raise ValueError(f"unknown temperature target: {target!r}")


def build_print_project(file_path: str, plate_index: int = 0) -> dict[str, Any]:
    return _print_cmd("project_file", param=file_path, plate_idx=plate_index)


def build_skip_object(obj_index: int) -> dict[str, Any]:
    return _print_cmd("skip_objects", param=json.dumps([obj_index]))
