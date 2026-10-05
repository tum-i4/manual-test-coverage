"""Configuration helpers for the native Frida runner."""

import os
from pathlib import Path


class RunnerConfig:  # pylint: disable=too-few-public-methods
    """Normalize the runner's bootstrap arguments and output paths."""

    def __init__(
        self,
        output_dir: str,
        function_infos: str,
        included_modules,
        agent_script_path,
    ):
        self.output_dir = Path(os.path.abspath(
            os.path.dirname(os.path.dirname(__file__)))) / output_dir
        self.function_infos = Path(os.path.abspath(function_infos))
        self.included_modules = [
            Path(module).resolve()
            for module in included_modules
        ]
        self.agent_script_path = Path(os.path.abspath(agent_script_path))
