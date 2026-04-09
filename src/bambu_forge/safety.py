"""G-code blocklist and per-printer temperature limit checks."""

from __future__ import annotations

from dataclasses import dataclass

from bambu_forge.printer_registry import PrinterModel

_BLOCKED_GCODES: dict[str, str] = {
    "M502": "firmware reset",
    "M500": "EEPROM save without prior M501",
}


@dataclass(frozen=True)
class GcodeValidationResult:
    blocked: bool
    reason: str


@dataclass(frozen=True)
class TempValidationResult:
    safe: bool
    reason: str


def validate_gcode(line: str, printer: PrinterModel) -> GcodeValidationResult:
    normalized = line.strip().upper()
    if not normalized:
        return GcodeValidationResult(blocked=False, reason="")
    first = normalized.split()[0]
    reason = _BLOCKED_GCODES.get(first)
    if reason is not None:
        return GcodeValidationResult(blocked=True, reason=reason)
    return GcodeValidationResult(blocked=False, reason="")


def validate_temperature(
    target: str, temp_c: float | int, printer: PrinterModel
) -> TempValidationResult:
    t = str(target).lower()
    temp = float(temp_c)

    if t == "nozzle":
        if temp > printer.nozzle_temp_max:
            return TempValidationResult(
                safe=False,
                reason=f"nozzle target {temp}°C exceeds max {printer.nozzle_temp_max}°C",
            )
        return TempValidationResult(safe=True, reason="")

    if t == "bed":
        if temp > printer.bed_temp_max:
            return TempValidationResult(
                safe=False,
                reason=f"bed target {temp}°C exceeds max {printer.bed_temp_max}°C",
            )
        return TempValidationResult(safe=True, reason="")

    if t == "chamber":
        if printer.chamber_temp_max is None:
            return TempValidationResult(
                safe=False,
                reason="Printer has no chamber; chamber temperature not supported",
            )
        if temp > printer.chamber_temp_max:
            return TempValidationResult(
                safe=False,
                reason=(
                    f"chamber target {temp}°C exceeds max {printer.chamber_temp_max}°C"
                ),
            )
        return TempValidationResult(safe=True, reason="")

    return TempValidationResult(safe=False, reason=f"unknown temperature target: {target!r}")
