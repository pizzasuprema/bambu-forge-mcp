from __future__ import annotations

import copy
import json
import ssl
import threading
import time
import uuid
from typing import Any

from paho.mqtt.client import CallbackAPIVersion, Client as MqttClient

_MOCK_STATUS: dict[str, Any] = {
    "print": {
        "gcode_state": "IDLE",
        "nozzle_temper": 24,
        "nozzle_target_temper": 0,
        "bed_temper": 23,
        "bed_target_temper": 0,
        "layer_num": 0,
        "total_layer_num": 0,
        "mc_percent": 0,
        "mc_remaining_time": 0,
        "subtask_name": "",
        "big_fan1_speed": "0",
        "big_fan2_speed": "0",
        "cooling_fan_speed": "0",
        "heatbreak_fan_speed": "0",
    },
    "ams": {
        "ams": [
            {
                "id": "0",
                "humidity": "5",
                "temp": "24",
                "tray": [],
            }
        ]
    },
}


def _sequence_id() -> str:
    return uuid.uuid4().hex[:8]


class BambuMqttClient:
    def __init__(
        self,
        host: str,
        access_code: str,
        serial: str,
        port: int = 8883,
        mock: bool = False,
    ) -> None:
        self.host = host
        self._access_code = access_code
        self.serial = serial
        self.port = port
        self._mock = mock
        self.report_topic = f"device/{serial}/report"
        self.request_topic = f"device/{serial}/request"
        self._client: MqttClient | None = None
        self._connected = False
        self._lock = threading.Lock()
        self._cached_status: dict[str, Any] | None = None
        self._status_updated_at: float | None = None
        if mock:
            self._cached_status = copy.deepcopy(_MOCK_STATUS)
            self._status_updated_at = time.monotonic()

    @property
    def is_connected(self) -> bool:
        return self._connected

    def _build_pushall(self) -> str:
        return json.dumps({"pushing": {"command": "pushall"}})

    def _build_print_command(self, command: str, **kwargs: Any) -> str:
        body: dict[str, Any] = {"command": command, "sequence_id": _sequence_id()}
        body.update(kwargs)
        return json.dumps({"print": body})

    def _build_system_command(self, command: str, **kwargs: Any) -> str:
        body: dict[str, Any] = {"command": command, "sequence_id": _sequence_id()}
        body.update(kwargs)
        return json.dumps({"system": body})

    def _on_message(self, _client: MqttClient, _userdata: Any, msg: Any) -> None:
        try:
            payload = json.loads(msg.payload.decode("utf-8"))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return
        if not isinstance(payload, dict):
            return

        with self._lock:
            if self._cached_status is None:
                self._cached_status = {}

            updated = False
            for key in ("print", "ams", "hms"):
                update = payload.get(key)
                if update is None:
                    continue
                if isinstance(update, list):
                    self._cached_status[key] = update
                    updated = True
                elif isinstance(update, dict):
                    slot = self._cached_status.setdefault(key, {})
                    if isinstance(slot, dict):
                        slot.update(update)
                    else:
                        self._cached_status[key] = update
                    updated = True

            if updated:
                self._status_updated_at = time.monotonic()

    def _on_disconnect(self, _client: MqttClient, _userdata: Any, *args: Any) -> None:
        self._connected = False

    def connect(self) -> None:
        if self._mock:
            self._connected = True
            return
        if self._connected and self._client is not None:
            return
        if self._client is not None:
            self._client.loop_stop()
            self._client.disconnect()
        client = MqttClient(callback_api_version=CallbackAPIVersion.VERSION2)
        client.username_pw_set("bblp", self._access_code)
        tls_context = ssl.create_default_context()
        tls_context.check_hostname = False
        tls_context.verify_mode = ssl.CERT_NONE
        client.tls_set_context(tls_context)
        client.on_message = self._on_message
        client.on_disconnect = self._on_disconnect
        client.connect(self.host, self.port, keepalive=60)
        client.subscribe(self.report_topic)
        client.loop_start()
        self._client = client
        self._connected = True

    def disconnect(self) -> None:
        if self._client is not None:
            self._client.loop_stop()
            self._client.disconnect()
            self._client = None
        self._connected = False

    def request_pushall(self) -> None:
        payload = self._build_pushall()
        if self._mock:
            with self._lock:
                self._status_updated_at = time.monotonic()
            return
        self.publish_command(payload)

    def publish_command(self, payload: str) -> None:
        if self._mock:
            return
        if self._client is None:
            raise RuntimeError("MQTT client is not connected")
        self._client.publish(self.request_topic, payload)

    def get_cached_status(self, max_age_seconds: float = 5.0) -> dict[str, Any] | None:
        if not self._connected:
            try:
                self.connect()
            except Exception:
                pass
        now = time.monotonic()
        with self._lock:
            stale = (
                self._cached_status is None
                or self._status_updated_at is None
                or (now - self._status_updated_at) > max_age_seconds
            )
        if stale:
            self.request_pushall()
        with self._lock:
            return copy.deepcopy(self._cached_status) if self._cached_status else None
