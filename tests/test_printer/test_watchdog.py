import time

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
