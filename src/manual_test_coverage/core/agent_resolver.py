"""Resolve platform-specific Frida agent scripts."""

import platform
from pathlib import Path

AGENT_DIR = Path(__file__).resolve().parents[1] / "agents"

AGENTS_BY_SYSTEM = {
    "Darwin": "darwin.js",
    "Linux": "linux.js",
    "Windows": "windows.js",
}


def resolve_agent_script_path(system=None, agent_script_path=None):
    """Return the Frida agent script for the requested platform."""
    if agent_script_path:
        return Path(agent_script_path).expanduser().resolve()

    system = system or platform.system()
    try:
        agent_name = AGENTS_BY_SYSTEM[system]
    except KeyError as exc:
        raise RuntimeError(f"Unsupported platform: {system}") from exc

    return AGENT_DIR / agent_name
