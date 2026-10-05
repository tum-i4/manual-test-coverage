import sys
from pathlib import Path

from manual_test_coverage.cli import build_runner

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src" / "coverage-agent"))


def test_build_runner_uses_target_executable_when_no_regex_provided(tmp_path):
    target_path = tmp_path / "demo.exe"
    target_path.write_text("demo", encoding="utf-8")

    class Args:
        target = str(target_path)
        output_dir = "reports"
        included_modules = None
        function_infos = str(tmp_path)
        pid = "8123"
        agent_script = None

    runner = build_runner(Args())

    assert runner._config.output_dir.name == "reports"
    assert runner._pid == 8123
    assert runner._config.included_modules == [target_path.resolve()]
    assert runner._config.agent_script_path.exists()


def test_build_runner_uses_custom_agent_script(tmp_path):
    target_path = tmp_path / "demo.exe"
    target_path.write_text("demo", encoding="utf-8")
    custom_agent = tmp_path / "agent.js"
    custom_agent.write_text("// custom", encoding="utf-8")

    class Args:
        target = str(target_path)
        output_dir = "reports"
        included_modules = None
        function_infos = str(tmp_path)
        pid = "8123"
        agent_script = str(custom_agent)

    runner = build_runner(Args())

    assert runner._config.agent_script_path == custom_agent.resolve()
