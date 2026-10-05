"""CLI bootstrap helpers for the native Frida coverage tool."""

import argparse
import os
import re
from pathlib import Path

from manual_test_coverage.core.agent_resolver import resolve_agent_script_path
from manual_test_coverage.core.runner import FridaRunner
from manual_test_coverage.core.runner_config import RunnerConfig


def parse_arguments():
    """Parse command line arguments for the native-only coverage tool."""
    parser = argparse.ArgumentParser(
        description="Run native Frida coverage recording for manual tests.")
    parser.add_argument("--target", "-t", required=True,
                        help="Path to the target native executable.")
    parser.add_argument("--function_infos", "-f", required=True,
                        help="Directory containing the .info files with function offsets.")
    parser.add_argument("--output_dir", "-o", default="coverage_reports",
                        help="Directory where coverage reports will be written.")
    parser.add_argument("--included_modules", "-i",
                        help="Regex of modules to instrument. Defaults to the target executable.")
    parser.add_argument("--pid", "-p", default=8123,
                        help="Target PID to trace.")
    parser.add_argument("--agent_script", "--agent-script",
                        help="Path to a custom Frida agent script.")
    return parser.parse_args()


def get_included_modules(directory: str, regex: str):
    """Resolve the modules that should be covered using the requested regex."""
    pattern = re.compile(regex)
    return [
        Path(directory, entry).resolve()
        for entry in Path(directory).iterdir()
        if pattern.match(entry.name)
    ]


def build_runner(args) -> FridaRunner:
    """Create a native Frida runner from parsed CLI arguments."""
    root_directory = os.path.dirname(args.target)
    included_modules = (
        [Path(args.target).resolve()]
        if args.included_modules is None
        else get_included_modules(directory=root_directory, regex=args.included_modules)
    )
    agent_script_path = resolve_agent_script_path(
        agent_script_path=getattr(args, "agent_script", None)
    )

    return FridaRunner(
        config=RunnerConfig(output_dir=args.output_dir,
                            function_infos=args.function_infos,
                            included_modules=included_modules,
                            agent_script_path=agent_script_path),
        pid=int(args.pid),
    )
