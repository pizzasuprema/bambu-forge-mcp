import json

from bambu_forge.printer.mqtt_client import BambuMqttClient


def test_mqtt_client_builds_connection_params():
    client = BambuMqttClient(
        host="192.168.1.50",
        access_code="abc12345",
        serial="01P00C123456789",
        mock=True,
    )
    assert client.host == "192.168.1.50"
    assert client.serial == "01P00C123456789"
    assert client.report_topic == "device/01P00C123456789/report"
    assert client.request_topic == "device/01P00C123456789/request"


def test_pushall_command_format():
    client = BambuMqttClient("h", "c", "S", mock=True)
    payload = json.loads(client._build_pushall())
    assert payload == {"pushing": {"command": "pushall"}}


def test_mock_status_returns_idle():
    client = BambuMqttClient("h", "c", "S", mock=True)
    status = client.get_cached_status()
    assert status is not None
    assert status["print"]["gcode_state"] == "IDLE"
    assert "nozzle_temper" in status["print"]


def test_publish_command_format():
    client = BambuMqttClient("h", "c", "S", mock=True)
    raw = client._build_print_command("pause")
    data = json.loads(raw)
    assert data["print"]["command"] == "pause"
    assert data["print"]["sequence_id"]
    assert len(str(data["print"]["sequence_id"])) >= 8
