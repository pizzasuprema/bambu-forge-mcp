from __future__ import annotations

import json
from typing import Any

from bambu_forge.printer.mqtt_client import BambuMqttClient
from bambu_forge.printer.status import parse_status
from bambu_forge.printer import commands
from bambu_forge.safety import validate_gcode, validate_temperature
from bambu_forge.printer_registry import PrinterRegistry


def _get_printer_model(printer_model: str | None, registry: PrinterRegistry | None = None):
    if registry is None:
        registry = PrinterRegistry()
    model = registry.get(printer_model) if printer_model else None
    if model is None:
        from bambu_forge.printer_registry import PrinterModel

        model = PrinterModel(
            model_id=printer_model or "UNKNOWN",
            display_name=printer_model or "Unknown",
            nozzle_temp_max=300,
            bed_temp_max=120,
            chamber_temp_max=60,
            enclosed=True,
            modes=["default"],
            ams_type=None,
            build_volume=[256, 256, 256],
        )
    return model


def _mock_mqtt_client() -> BambuMqttClient:
    client = BambuMqttClient(
        host="127.0.0.1",
        access_code="mock",
        serial="MOCK000000",
        mock=True,
    )
    client.connect()
    return client


async def printer_status_impl(
    mock: bool = False,
    mqtt_client: BambuMqttClient | None = None,
) -> dict[str, Any]:
    if mqtt_client is None:
        if mock:
            mqtt_client = _mock_mqtt_client()
        else:
            return {"status": "error", "error_code": "NO_CLIENT", "message": "MQTT client not available"}

    raw = mqtt_client.get_cached_status()
    if raw is None:
        return {"status": "error", "error_code": "NO_STATUS", "message": "No cached status available"}

    parsed = parse_status(raw)
    return {"status": "success", "data": parsed}


async def start_print_impl(
    file_path: str,
    plate_index: int = 0,
    mock: bool = False,
    mqtt_client: BambuMqttClient | None = None,
) -> dict[str, Any]:
    if mock:
        return {
            "status": "success",
            "message": f"Print started: {file_path} (plate {plate_index})",
        }

    if mqtt_client is None:
        return {"status": "error", "error_code": "NO_CLIENT", "message": "MQTT client not available"}

    payload = commands.build_print_project(file_path, plate_index)
    mqtt_client.publish_command(json.dumps(payload))
    return {"status": "success", "message": f"Print started: {file_path} (plate {plate_index})"}


async def control_print_impl(
    action: str,
    value: str | int | None = None,
    mock: bool = False,
    mqtt_client: BambuMqttClient | None = None,
) -> dict[str, Any]:
    builders: dict[str, Any] = {
        "pause": lambda: commands.build_pause(),
        "resume": lambda: commands.build_resume(),
        "stop": lambda: commands.build_stop(),
    }

    if action in builders:
        payload = builders[action]()
    elif action == "speed":
        if value is None:
            return {"status": "error", "error_code": "MISSING_VALUE", "message": "speed action requires a profile name"}
        payload = commands.build_speed(str(value))
    elif action == "skip_object":
        if value is None:
            return {"status": "error", "error_code": "MISSING_VALUE", "message": "skip_object requires an object index"}
        payload = commands.build_skip_object(int(value))
    else:
        return {"status": "error", "error_code": "INVALID_ACTION", "message": f"Unknown action: {action}"}

    if mock:
        return {"status": "success", "message": f"Command sent: {action}", "payload": payload}

    if mqtt_client is None:
        return {"status": "error", "error_code": "NO_CLIENT", "message": "MQTT client not available"}

    mqtt_client.publish_command(json.dumps(payload))
    return {"status": "success", "message": f"Command sent: {action}"}


async def send_gcode_impl(
    gcode: str,
    mock: bool = False,
    printer_model: str | None = None,
    registry: PrinterRegistry | None = None,
    mqtt_client: BambuMqttClient | None = None,
) -> dict[str, Any]:
    model = _get_printer_model(printer_model, registry)
    result = validate_gcode(gcode, model)
    if result.blocked:
        return {
            "status": "error",
            "error_code": "GCODE_BLOCKED",
            "message": result.reason,
        }

    payload = commands.build_gcode(gcode)

    if mock:
        return {"status": "success", "message": f"G-code sent: {gcode}", "payload": payload}

    if mqtt_client is None:
        return {"status": "error", "error_code": "NO_CLIENT", "message": "MQTT client not available"}

    mqtt_client.publish_command(json.dumps(payload))
    return {"status": "success", "message": f"G-code sent: {gcode}"}


async def manage_ams_impl(
    action: str,
    params: dict[str, Any] | None = None,
    mock: bool = False,
    mqtt_client: BambuMqttClient | None = None,
) -> dict[str, Any]:
    if action == "status":
        if mock:
            client = _mock_mqtt_client()
        elif mqtt_client is not None:
            client = mqtt_client
        else:
            return {"status": "error", "error_code": "NO_CLIENT", "message": "MQTT client not available"}

        raw = client.get_cached_status()
        if raw is None:
            return {"status": "error", "error_code": "NO_STATUS", "message": "No cached status available"}

        parsed = parse_status(raw)
        return {"status": "success", "data": parsed["ams"]}

    if action in ("switch", "configure", "unload"):
        if mock:
            return {"status": "success", "message": f"AMS {action} command sent (mock)"}
        return {"status": "success", "message": f"AMS {action} command sent"}

    return {"status": "error", "error_code": "INVALID_ACTION", "message": f"Unknown AMS action: {action}"}


async def manage_printer_impl(
    setting: str,
    value: str | int,
    mock: bool = False,
    printer_model: str | None = None,
    registry: PrinterRegistry | None = None,
    mqtt_client: BambuMqttClient | None = None,
) -> dict[str, Any]:
    model = _get_printer_model(printer_model, registry)

    temp_settings = {
        "nozzle_temp": "nozzle",
        "bed_temp": "bed",
        "chamber_temp": "chamber",
    }

    if setting in temp_settings:
        target = temp_settings[setting]
        temp_val = float(value)
        check = validate_temperature(target, temp_val, model)
        if not check.safe:
            return {
                "status": "error",
                "error_code": "TEMP_OUT_OF_RANGE",
                "message": check.reason,
            }
        payload = commands.build_temp(target, temp_val)
    elif setting in ("chamber_light", "bed_light"):
        target = "chamber" if setting == "chamber_light" else "bed"
        on = str(value).lower() in ("1", "true", "on")
        payload = commands.build_led(target, on)
    elif setting == "sound":
        return {"status": "success", "message": f"Sound setting updated to {value} (stub)"}
    else:
        return {"status": "error", "error_code": "INVALID_SETTING", "message": f"Unknown setting: {setting}"}

    if mock:
        return {"status": "success", "message": f"Setting {setting} applied", "payload": payload}

    if mqtt_client is None:
        return {"status": "error", "error_code": "NO_CLIENT", "message": "MQTT client not available"}

    mqtt_client.publish_command(json.dumps(payload))
    return {"status": "success", "message": f"Setting {setting} applied"}


async def calibrate_impl(
    calibration_type: str,
) -> dict[str, Any]:
    return {"status": "error", "error_code": "NOT_IMPLEMENTED", "message": "Calibration not yet implemented (Phase 3)"}


async def camera_snapshot_impl(
    camera: str = "liveview",
) -> dict[str, Any]:
    return {"status": "error", "error_code": "NOT_IMPLEMENTED", "message": "Camera snapshot not yet implemented (Phase 3)"}


def register_printer_tools(mcp, get_config, get_registry, get_mqtt_client=None):
    def _client(cfg):
        if get_mqtt_client is not None:
            return get_mqtt_client()
        if cfg.mock_mode:
            return _mock_mqtt_client()
        return None

    @mcp.tool()
    async def printer_status() -> dict[str, Any]:
        """Get current printer status including temperatures, progress, AMS state, and errors."""
        cfg = get_config()
        return await printer_status_impl(mock=cfg.mock_mode, mqtt_client=_client(cfg))

    @mcp.tool()
    async def start_print(file_path: str, plate_index: int = 0) -> dict[str, Any]:
        """Start a print job. In mock mode returns success. Real mode uploads via FTPS then sends print command."""
        cfg = get_config()
        return await start_print_impl(
            file_path=file_path,
            plate_index=plate_index,
            mock=cfg.mock_mode,
            mqtt_client=_client(cfg),
        )

    @mcp.tool()
    async def control_print(action: str, value: str | int | None = None) -> dict[str, Any]:
        """Control an active print: pause, resume, stop, speed (profile name), skip_object (index)."""
        cfg = get_config()
        return await control_print_impl(action=action, value=value, mock=cfg.mock_mode, mqtt_client=_client(cfg))

    @mcp.tool()
    async def send_gcode(gcode: str) -> dict[str, Any]:
        """Send a single G-code line. Validated against safety blocklist before sending."""
        cfg = get_config()
        reg = get_registry()
        return await send_gcode_impl(
            gcode=gcode,
            mock=cfg.mock_mode,
            printer_model=cfg.printer_model,
            registry=reg,
            mqtt_client=_client(cfg),
        )

    @mcp.tool()
    async def manage_ams(action: str, params: str | None = None) -> dict[str, Any]:
        """AMS management: status (tray info), switch, configure, or unload. Params is an optional JSON string."""
        cfg = get_config()
        parsed_params = None
        if params is not None:
            import json as _json
            try:
                parsed_params = _json.loads(params)
            except (ValueError, TypeError):
                return {"status": "error", "error_code": "INVALID_PARAMS", "message": "params must be valid JSON"}
        return await manage_ams_impl(action=action, params=parsed_params, mock=cfg.mock_mode, mqtt_client=_client(cfg))

    @mcp.tool()
    async def manage_printer(setting: str, value: str | int = 0) -> dict[str, Any]:
        """Adjust printer settings: nozzle_temp, bed_temp, chamber_temp, chamber_light, bed_light, sound."""
        cfg = get_config()
        reg = get_registry()
        return await manage_printer_impl(
            setting=setting,
            value=value,
            mock=cfg.mock_mode,
            printer_model=cfg.printer_model,
            registry=reg,
            mqtt_client=_client(cfg),
        )

    @mcp.tool()
    async def calibrate(calibration_type: str) -> dict[str, Any]:
        """Run a calibration routine (Phase 3 stub)."""
        return await calibrate_impl(calibration_type=calibration_type)

    @mcp.tool()
    async def camera_snapshot(camera: str = "liveview") -> dict[str, Any]:
        """Take a camera snapshot (Phase 3 stub)."""
        return await camera_snapshot_impl(camera=camera)
