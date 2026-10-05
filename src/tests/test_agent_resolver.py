from pathlib import Path

import pytest

from manual_test_coverage.core.agent_resolver import resolve_agent_script_path


def test_resolve_agent_script_path_uses_platform_agent():
    result = resolve_agent_script_path(system="Linux")

    assert result.name == "linux.js"
    assert result.exists()


def test_resolve_agent_script_path_uses_custom_agent(tmp_path: Path):
    custom_agent = tmp_path / "custom.js"
    custom_agent.write_text("// custom", encoding="utf-8")

    result = resolve_agent_script_path(agent_script_path=custom_agent)

    assert result == custom_agent.resolve()


def test_resolve_agent_script_path_rejects_unsupported_platform():
    with pytest.raises(RuntimeError, match="Unsupported platform"):
        resolve_agent_script_path(system="Solaris")
