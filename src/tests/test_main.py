import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "coverage-agent"))

from manual_test_coverage.main import parse_arguments


def test_parse_arguments_accepts_required_native_options(monkeypatch):
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "coverage-agent",
            "--target",
            "./bin/demo.exe",
            "--function_infos",
            "./info",
            "--output_dir",
            "./reports",
            "--pid",
            "8123",
        ],
    )

    args = parse_arguments()

    assert args.target == "./bin/demo.exe"
    assert args.function_infos == "./info"
    assert args.output_dir == "./reports"
    assert args.pid == "8123"
