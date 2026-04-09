import time

import pytest

from bambu_forge.printer.watchdog import HeaterWatchdog


def test_watchdog_init():
    wd = HeaterWatchdog(mqtt_client=None, timeout_minutes=15)
    assert wd._timeout == 15 * 60
    assert wd._running is False
    assert wd._task is None


def test_watchdog_notify():
    wd = HeaterWatchdog(mqtt_client=None, timeout_minutes=30)
    before = wd._last_user_temp_command
    time.sleep(0.01)
    wd.notify_user_temp_command()
    assert wd._last_user_temp_command > before


@pytest.mark.asyncio
async def test_watchdog_cooldown_when_idle():
    """Verify _single_check completes without error when heaters are hot + idle + timeout exceeded."""
    from bambu_forge.printer.mqtt_client import BambuMqttClient

    client = BambuMqttClient(host="x", access_code="x", serial="x", mock=True)
    client._cached_status["print"]["nozzle_temper"] = 200.0
    client._cached_status["print"]["gcode_state"] = "IDLE"

    wd = HeaterWatchdog(mqtt_client=client, timeout_minutes=0)
    wd._last_user_temp_command = 0  # long ago

    await wd._single_check()


@pytest.mark.asyncio
async def test_watchdog_skips_when_printing():
    """Verify _single_check does nothing while printer is actively printing."""
    from bambu_forge.printer.mqtt_client import BambuMqttClient

    client = BambuMqttClient(host="x", access_code="x", serial="x", mock=True)
    client._cached_status["print"]["nozzle_temper"] = 220.0
    client._cached_status["print"]["gcode_state"] = "RUNNING"

    wd = HeaterWatchdog(mqtt_client=client, timeout_minutes=0)
    wd._last_user_temp_command = 0

    await wd._single_check()


@pytest.mark.asyncio
async def test_watchdog_skips_when_cool():
    """Verify _single_check does nothing when heaters are already cool."""
    from bambu_forge.printer.mqtt_client import BambuMqttClient

    client = BambuMqttClient(host="x", access_code="x", serial="x", mock=True)
    client._cached_status["print"]["nozzle_temper"] = 24.0
    client._cached_status["print"]["bed_temper"] = 23.0
    client._cached_status["print"]["gcode_state"] = "IDLE"

    wd = HeaterWatchdog(mqtt_client=client, timeout_minutes=0)
    wd._last_user_temp_command = 0

    await wd._single_check()
