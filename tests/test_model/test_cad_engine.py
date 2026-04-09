import os

import pytest

from bambu_forge.model.cad_engine import execute_cadquery


CADQUERY_BOX = """\
import cadquery as cq

result = cq.Workplane("XY").box(10, 20, 5)
cq.exporters.export(result, OUTPUT_PATH)
"""


def test_execute_cadquery_code(tmp_path):
    output = tmp_path / "box.stl"
    result = execute_cadquery(CADQUERY_BOX, str(output), str(tmp_path), timeout=120)

    assert result["success"] is True
    assert output.exists()
    assert output.stat().st_size > 0


def test_execute_timeout(tmp_path):
    code = "import time; time.sleep(120)"
    output = tmp_path / "never.stl"
    result = execute_cadquery(code, str(output), str(tmp_path), timeout=2)

    assert result["success"] is False
    assert "timeout" in result["error"].lower()


def test_execute_syntax_error(tmp_path):
    code = "def broken(:"
    output = tmp_path / "bad.stl"
    result = execute_cadquery(code, str(output), str(tmp_path), timeout=10)

    assert result["success"] is False
    assert result["error"]
