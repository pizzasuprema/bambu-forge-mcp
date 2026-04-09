from bambu_forge.printer import commands


def test_pause_command():
    cmd = commands.build_pause()
    assert cmd["print"]["command"] == "pause"
    assert "sequence_id" in cmd["print"]
    assert len(cmd["print"]["sequence_id"]) == 8


def test_resume_command():
    cmd = commands.build_resume()
    assert cmd["print"]["command"] == "resume"


def test_stop_command():
    cmd = commands.build_stop()
    assert cmd["print"]["command"] == "stop"


def test_speed_command():
    cmd = commands.build_speed("sport")
    assert cmd["print"]["command"] == "print_speed"
    assert cmd["print"]["param"] == "sport"


def test_gcode_command():
    cmd = commands.build_gcode("G28")
    assert cmd["print"]["command"] == "gcode_line"
    assert cmd["print"]["param"] == "G28\n"


def test_led_command():
    cmd = commands.build_led("chamber", True)
    assert cmd["system"]["command"] == "ledctrl"


def test_temp_command():
    cmd = commands.build_temp("nozzle", 200)
    assert cmd["print"]["command"] == "gcode_line"
    assert "M104" in cmd["print"]["param"]
