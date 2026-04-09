import json
import os

import pytest

from bambu_forge.model.cad_engine import execute_cadquery


CADQUERY_BOX = """\
import os, cadquery as cq

result = cq.Workplane("XY").box(10, 20, 5)
cq.exporters.export(result, os.environ["OUTPUT_PATH"])
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


CADQUERY_NO_EXPORT = """\
import cadquery as cq

result = cq.Workplane("XY").box(10, 20, 5)
"""


def test_auto_export_fires_when_result_assigned(tmp_path):
    """Code assigns `result` but never calls export(); auto-export should write the file."""
    output = tmp_path / "auto.stl"
    result = execute_cadquery(CADQUERY_NO_EXPORT, str(output), str(tmp_path), timeout=120)

    assert result["success"] is True
    assert output.exists()
    assert output.stat().st_size > 0


def test_auto_export_skips_when_already_exported(tmp_path):
    """If user code already exports, auto-export should not interfere."""
    output = tmp_path / "manual.stl"
    result = execute_cadquery(CADQUERY_BOX, str(output), str(tmp_path), timeout=120)

    assert result["success"] is True
    assert output.exists()
    assert output.stat().st_size > 0


def test_env_stripping(tmp_path, monkeypatch):
    monkeypatch.setenv("BAMBU_ACCESS_CODE", "supersecret")
    monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "alsosecret")
    code = '''
import os, json
result = {k: v for k, v in os.environ.items()}
with open(os.environ["OUTPUT_PATH"], "w") as f:
    json.dump(result, f)
'''
    output = tmp_path / "env.json"
    result = execute_cadquery(code, str(output), str(tmp_path))
    assert result["success"] is True
    env_data = json.loads(output.read_text())
    assert "BAMBU_ACCESS_CODE" not in env_data
    assert "AWS_SECRET_ACCESS_KEY" not in env_data
    assert "PATH" in env_data
