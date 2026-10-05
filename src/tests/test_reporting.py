import sys
from pathlib import Path

from manual_test_coverage.reporting.cobertura import to_cobertura_xml

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "coverage-agent"))


def test_to_cobertura_xml_writes_report(tmp_path: Path):
    coverage_data = {
        "demo": {
            "example.cpp": {
                "func_a": True,
                "func_b": False,
            }
        }
    }

    output_file = tmp_path / "coverage.xml"

    to_cobertura_xml(coverage_data, output_file)

    assert output_file.exists()
    content = output_file.read_text(encoding="utf-8")
    assert "<coverage" in content
    assert "demo" in content
    assert "func_a" in content
    assert "func_b" not in content
