"""Heater watchdog — cools down idle heaters after a configurable timeout."""

from __future__ import annotations

import asyncio
import json
import time


class HeaterWatchdog:
    def __init__(self, mqtt_client, timeout_minutes: int = 30):
        self._mqtt_client = mqtt_client
        self._timeout = timeout_minutes * 60
        self._last_user_temp_command = time.time()
        self._task: asyncio.Task | None = None
        self._running = False

    def notify_user_temp_command(self):
        """Call this when user explicitly sets a temperature."""
        self._last_user_temp_command = time.time()

    async def _check_loop(self):
        while self._running:
            await asyncio.sleep(60)
            if not self._mqtt_client or not self._mqtt_client.is_connected:
                continue

            status = self._mqtt_client.get_cached_status()
            if status is None:
                continue

            p = status.get("print", {})
            state = p.get("gcode_state", "UNKNOWN")

            if state in ("RUNNING", "PAUSE"):
                continue

            nozzle = p.get("nozzle_temper", 0)
            bed = p.get("bed_temper", 0)

            if nozzle <= 30 and bed <= 30:
                continue

            if time.time() - self._last_user_temp_command < self._timeout:
                continue

            from bambu_forge.printer.commands import build_temp

            if nozzle > 30:
                self._mqtt_client.publish_command(json.dumps(build_temp("nozzle", 0)))
            if bed > 30:
                self._mqtt_client.publish_command(json.dumps(build_temp("bed", 0)))

    def start(self):
        self._running = True
        self._task = asyncio.ensure_future(self._check_loop())

    def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
