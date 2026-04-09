"""Printer model registry: embedded fallback plus optional Bambu Studio JSON overlay."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping


@dataclass(frozen=True)
class PrinterModel:
    model_id: str
    display_name: str
    nozzle_temp_max: int
    bed_temp_max: int
    chamber_temp_max: int | None
    enclosed: bool
    modes: list[str]
    ams_type: str | None
    build_volume: list[int]
    dual_nozzle: bool = False


def _fallback_registry_path() -> Path:
    here = Path(__file__).resolve().parent
    wheel_data = here / "data" / "fallback_registry.json"
    if wheel_data.exists():
        return wheel_data
    return here.parent.parent / "data" / "fallback_registry.json"


def _printer_model_from_fallback_entry(model_id: str, entry: Mapping[str, Any]) -> PrinterModel:
    return PrinterModel(
        model_id=model_id,
        display_name=str(entry["display_name"]),
        nozzle_temp_max=int(entry["nozzle_temp_max"]),
        bed_temp_max=int(entry["bed_temp_max"]),
        chamber_temp_max=entry.get("chamber_temp_max"),
        enclosed=bool(entry["enclosed"]),
        modes=list(entry["modes"]),
        ams_type=entry.get("ams_type"),
        build_volume=[int(x) for x in entry["build_volume"]],
        dual_nozzle=bool(entry.get("dual_nozzle", False)),
    )


def _load_fallback() -> tuple[dict[str, PrinterModel], dict[str, str]]:
    path = _fallback_registry_path()
    raw = json.loads(path.read_text(encoding="utf-8"))
    model_id_map: dict[str, str] = dict(raw.get("model_id_map", {}))
    printers: dict[str, PrinterModel] = {}
    for mid, spec in raw["printers"].items():
        printers[mid] = _printer_model_from_fallback_entry(mid, spec)
    return printers, model_id_map


def _extract_bambu_studio_spec(data: dict[str, Any]) -> dict[str, Any]:
    for _key, value in data.items():
        if isinstance(value, dict) and (
            "model_id" in value or "display_name" in value or "print" in value
        ):
            return value
    raise ValueError("No printer spec dict found in Bambu Studio JSON")


def _range_max(range_val: Any, default: int) -> int:
    if isinstance(range_val, (list, tuple)) and len(range_val) >= 2:
        return int(range_val[1])
    return default


def _parse_bambu_studio_printer(
    path: Path,
    model_id_map: Mapping[str, str],
    base: PrinterModel | None = None,
) -> PrinterModel:
    data = json.loads(path.read_text(encoding="utf-8"))
    spec = _extract_bambu_studio_spec(data)
    file_model_id = str(spec.get("model_id", path.stem))
    canonical = model_id_map.get(file_model_id, file_model_id)

    print_block = spec.get("print") or {}
    nozzle_max = _range_max(print_block.get("nozzle_temp_range"), 300)
    bed_max = _range_max(print_block.get("bed_temp_range"), 100)
    chamber_range = print_block.get("chamber_temp_range")
    if chamber_range is None:
        chamber_range = spec.get("chamber_temp_range")
    chamber_max: int | None
    if isinstance(chamber_range, (list, tuple)) and len(chamber_range) >= 2:
        chamber_max = int(chamber_range[1])
    elif base is not None:
        chamber_max = base.chamber_temp_max
    else:
        chamber_max = None

    display_name = str(spec.get("display_name", canonical))
    enclosed = bool(spec.get("printer_is_enclosed", False))
    modes = list(spec.get("printer_modes") or [])
    if not modes and base is not None:
        modes = list(base.modes)

    ams_type = spec.get("ams_type")
    if ams_type is not None:
        ams_type = str(ams_type)
    elif base is not None:
        ams_type = base.ams_type

    bv = spec.get("build_volume") or spec.get("printable_area")
    if isinstance(bv, (list, tuple)) and len(bv) >= 3:
        build_volume = [int(bv[0]), int(bv[1]), int(bv[2])]
    elif base is not None:
        build_volume = list(base.build_volume)
    else:
        build_volume = [256, 256, 256]

    dual = bool(spec.get("dual_nozzle", base.dual_nozzle if base else False))

    return PrinterModel(
        model_id=canonical,
        display_name=display_name,
        nozzle_temp_max=nozzle_max,
        bed_temp_max=bed_max,
        chamber_temp_max=chamber_max,
        enclosed=enclosed,
        modes=modes,
        ams_type=ams_type,
        build_volume=build_volume,
        dual_nozzle=dual,
    )


class PrinterRegistry:
    def __init__(self, bambu_studio_path: str | Path | None = None) -> None:
        self._models, self._model_id_map = _load_fallback()
        if bambu_studio_path is not None:
            studio = Path(bambu_studio_path)
            printers_dir = studio / "printers"
            if printers_dir.is_dir():
                for json_path in sorted(printers_dir.glob("*.json")):
                    base = self._models.get(
                        _canonical_from_studio_path(json_path, self._model_id_map)
                    )
                    parsed = _parse_bambu_studio_printer(
                        json_path, self._model_id_map, base=base
                    )
                    self._models[parsed.model_id] = parsed

    def get(self, model_id: str) -> PrinterModel | None:
        return self._models.get(model_id)

    def list_models(self) -> list[str]:
        return sorted(self._models.keys())


def _canonical_from_studio_path(path: Path, model_id_map: Mapping[str, str]) -> str:
    stem = path.stem
    return model_id_map.get(stem, stem)
