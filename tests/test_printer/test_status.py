from bambu_forge.printer.status import parse_status


def test_parse_status_idle():
    raw = {
        "print": {
            "gcode_state": "IDLE",
            "mc_percent": 0,
            "mc_remaining_time": 0,
            "nozzle_temper": 25,
            "nozzle_target_temper": 0,
            "bed_temper": 25,
            "bed_target_temper": 0,
            "layer_num": 0,
            "total_layer_num": 0,
            "subtask_name": "",
            "spd_lvl": "2",
        },
        "ams": {"ams": [{"id": "0", "tray": []}]},
        "hms": [],
    }
    out = parse_status(raw)
    assert out["state"] == "IDLE"
    assert out["progress"] == 0
    assert out["nozzle"]["current"] == 25.0
    assert out["bed"]["current"] == 25.0
    assert out["ams"]["trays"] == []


def test_parse_status_printing():
    raw = {
        "print": {
            "gcode_state": "RUNNING",
            "mc_percent": 47,
            "mc_remaining_time": 68,
            "nozzle_temper": 220,
            "nozzle_target_temper": 220,
            "bed_temper": 65,
            "bed_target_temper": 65,
            "layer_num": 89,
            "total_layer_num": 187,
            "subtask_name": "phone_stand.3mf",
            "spd_lvl": "3",
            "obj_list": [{"name": "phone_stand", "identify_id": "0"}],
        },
        "ams": {
            "ams": [
                {
                    "tray": [
                        {
                            "tray_type": "PLA",
                            "tray_color": "161616FF",
                            "remain": 72,
                        }
                    ]
                }
            ]
        },
        "hms": [],
    }
    out = parse_status(raw)
    assert out["state"] == "RUNNING"
    assert out["progress"] == 47
    assert out["remaining_minutes"] == 68
    assert out["layer"]["current"] == 89
    assert out["layer"]["total"] == 187
    assert out["job_name"] == "phone_stand.3mf"
    assert len(out["ams"]["trays"]) == 1
    assert out["ams"]["trays"][0]["type"] == "PLA"
    assert len(out["objects"]) == 1
    assert out["objects"][0]["name"] == "phone_stand"


def test_parse_status_nested_ams_hms_in_print():
    """pushall messages nest ams/hms inside the print block."""
    raw = {
        "print": {
            "gcode_state": "RUNNING",
            "mc_percent": 50,
            "mc_remaining_time": 30,
            "nozzle_temper": 210,
            "nozzle_target_temper": 210,
            "bed_temper": 60,
            "bed_target_temper": 60,
            "ams": {
                "ams": [
                    {
                        "tray": [
                            {
                                "tray_type": "PETG",
                                "tray_color": "FF0000FF",
                                "remain": 55,
                            }
                        ]
                    }
                ]
            },
            "hms": [{"code": "0300010001", "msg": "AMS filament run out"}],
        },
    }
    out = parse_status(raw)
    assert len(out["ams"]["trays"]) == 1
    assert out["ams"]["trays"][0]["type"] == "PETG"
    assert len(out["errors"]) == 1
    assert out["errors"][0]["code"] == "0300010001"
