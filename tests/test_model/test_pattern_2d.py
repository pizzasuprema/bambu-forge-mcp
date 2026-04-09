import os

import pytest

from bambu_forge.model.pattern_2d import generate_2d_pattern


SVG_CODE = """\
import svgwrite
dwg = svgwrite.Drawing(OUTPUT_PATH, size=("100mm", "100mm"))
dwg.add(dwg.rect(insert=("10mm", "10mm"), size=("80mm", "80mm"), fill="none", stroke="black"))
dwg.save()
"""

DXF_CODE = """\
import ezdxf
doc = ezdxf.new()
msp = doc.modelspace()
msp.add_line((0, 0), (100, 100))
doc.saveas(OUTPUT_PATH)
"""


def test_generate_svg(tmp_path):
    output = str(tmp_path / "pattern.svg")
    result = generate_2d_pattern(SVG_CODE, "svg", output, str(tmp_path), timeout=30)

    assert result["status"] == "success"
    assert result["file_path"] == output
    assert os.path.exists(output)
    assert os.path.getsize(output) > 0


def test_generate_dxf(tmp_path):
    output = str(tmp_path / "pattern.dxf")
    result = generate_2d_pattern(DXF_CODE, "dxf", output, str(tmp_path), timeout=30)

    assert result["status"] == "success"
    assert result["file_path"] == output
    assert os.path.exists(output)
    assert os.path.getsize(output) > 0
