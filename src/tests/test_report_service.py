import re
from datetime import datetime, timedelta
from pathlib import Path

from manual_test_coverage.core.coverage_store import CoverageStore
from manual_test_coverage.core.report_service import ReportService


def test_report_service_writes_cobertura_report(tmp_path: Path):
    store = CoverageStore()
    store.add("demo.exe", [10, 30])

    function_infos = {
        "demo.exe": [
            ("func_a", "demo.exe", "demo.cpp", 10),
            ("func_b", "demo.exe", "demo.cpp", 20),
            ("func_c", "demo.exe", "demo.cpp", 30),
        ]
    }

    output_file = tmp_path / "report.xml"
    service = ReportService()

    result = service.write_report(store, function_infos, output_file)

    assert result == output_file
    assert output_file.exists()
    text = output_file.read_text(encoding="utf-8")
    assert "<coverage" in text
    assert "func_a" in text
    assert "func_c" in text
    assert "func_b" not in text


def test_report_service_creates_output_directory(tmp_path: Path):
    store = CoverageStore()
    store.add("demo.exe", [10])

    function_infos = {
        "demo.exe": [
            ("func_a", "demo.exe", "demo.cpp", 10),
        ]
    }

    output_file = tmp_path / "nested" / "coverage.xml"
    service = ReportService()

    result = service.write_report(store, function_infos, output_file)

    assert result == output_file
    assert output_file.exists()
    assert output_file.parent.exists()


def test_report_service_builds_test_output_dir(tmp_path: Path):
    service = ReportService()

    before = datetime.now().replace(microsecond=0)
    result = service.build_report_dir(
        output_root=tmp_path,
        tester_id="tester-1",
        test_name="sample-test",
        start_pid=4242,
    )
    after = datetime.now().replace(microsecond=0) + timedelta(seconds=1)

    assert result.parent == tmp_path / "tester-1"
    assert result.exists()

    match = re.fullmatch(r"sample-test_(\d{4}-\d{2}-\d{2}-\d{6})_4242", result.name)
    assert match is not None, result.name

    timestamp = datetime.strptime(match.group(1), "%Y-%m-%d-%H%M%S")
    assert before <= timestamp <= after
