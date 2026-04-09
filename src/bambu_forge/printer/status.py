from __future__ import annotations

import json
from typing import Any


def _as_float(value: Any, default: float = 0.0) -> float:
    if value is None or value == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _as_int(value: Any, default: int = 0) -> int:
    if value is None or value == "":
        return default
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _flatten_ams_trays(ams_root: Any) -> list[dict[str, Any]]:
    if not isinstance(ams_root, dict):
        return []
    units = ams_root.get("ams")
    if not isinstance(units, list):
        return []
    trays: list[dict[str, Any]] = []
    for unit in units:
        if not isinstance(unit, dict):
            continue
        tray_list = unit.get("tray")
        if not isinstance(tray_list, list):
            continue
        for slot in tray_list:
            if not isinstance(slot, dict):
                continue
            trays.append(
                {
                    "type": str(slot.get("tray_type", "") or ""),
                    "color": str(slot.get("tray_color", "") or ""),
                    "remaining_percent": _as_float(slot.get("remain"), 0.0),
                }
            )
    return trays


def _parse_objects(obj_list: Any) -> list[dict[str, Any]]:
    if obj_list is None:
        return []
    if isinstance(obj_list, str):
        try:
            obj_list = json.loads(obj_list)
        except (json.JSONDecodeError, TypeError):
            return []
    if not isinstance(obj_list, list):
        return []
    out: list[dict[str, Any]] = []
    for item in obj_list:
        if not isinstance(item, dict):
            continue
        name = str(item.get("name", "") or "")
        idx_raw = item.get("identify_id", item.get("index", 0))
        out.append({"index": _as_int(idx_raw, 0), "name": name})
    return out


def parse_status(raw: dict[str, Any]) -> dict[str, Any]:
    p = raw.get("print") if isinstance(raw.get("print"), dict) else {}
    ams_block = raw.get("ams")
    hms = raw.get("hms")
    errors: list[Any] = list(hms) if isinstance(hms, list) else []

    nozzle_cur = _as_float(p.get("nozzle_temper"))
    nozzle_tgt = _as_float(p.get("nozzle_target_temper"))
    bed_cur = _as_float(p.get("bed_temper"))
    bed_tgt = _as_float(p.get("bed_target_temper"))
    chamber_cur = _as_float(p.get("chamber_temper"))

    return {
        "state": str(p.get("gcode_state", "") or ""),
        "progress": _as_int(p.get("mc_percent"), 0),
        "remaining_minutes": _as_int(p.get("mc_remaining_time"), 0),
        "nozzle": {"current": nozzle_cur, "target": nozzle_tgt},
        "bed": {"current": bed_cur, "target": bed_tgt},
        "chamber": {"current": chamber_cur},
        "layer": {
            "current": _as_int(p.get("layer_num"), 0),
            "total": _as_int(p.get("total_layer_num"), 0),
        },
        "speed": str(p.get("spd_lvl", "") or ""),
        "job_name": str(p.get("subtask_name", "") or ""),
        "ams": {"trays": _flatten_ams_trays(ams_block)},
        "errors": errors,
        "objects": _parse_objects(p.get("obj_list")),
    }
