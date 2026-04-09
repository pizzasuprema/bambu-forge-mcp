"""Heater watchdog — cools down idle heaters after a configurable timeout."""

from __future__ import annotations

import asyncio
import json
import time

from bambu_forge.printer.commands import build_temp


class HeaterWatchdog:
    def __init__(self, mqtt_client, timeout_minutes: int = 30):
        self._mqtt_client = mqtt_client
        self._timeout = timeout_minutes * 60
        self._last_user_temp_command = time.monotonic()
        self._task: asyncio.Task | None = None
        self._running = False

    def notify_user_temp_command(self):
        """Call this when user explicitly sets a temperature."""
        self._last_user_temp_command = time.monotonic()

    async def _single_check(self):
        """Run one iteration of the heater check logic. Testable without the loop."""
        if not self._mqtt_client or not self._mqtt_client.is_connected:
            return

        status = self._mqtt_client.get_cached_status()
        if status is None:
            return

        p = status.get("print", {})
        state = p.get("gcode_state", "UNKNOWN")

        if state in ("RUNNING", "PAUSE"):
            return

        nozzle = p.get("nozzle_temper", 0)
        bed = p.get("bed_temper", 0)

        if nozzle <= 30 and bed <= 30:
            return

        if time.monotonic() - self._last_user_temp_command < self._timeout:
            return

        if nozzle > 30:
            self._mqtt_client.publish_command(json.dumps(build_temp("nozzle", 0)))
        if bed > 30:
            self._mqtt_client.publish_command(json.dumps(build_temp("bed", 0)))

    async def _check_loop(self):
        while self._running:
            await asyncio.sleep(60)
            await self._single_check()

    def start(self):
        self._running = True
        self._task = asyncio.ensure_future(self._check_loop())

    def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
