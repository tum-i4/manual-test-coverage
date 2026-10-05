"""Registry for native module metadata used by coverage instrumentation."""

import logging
from pathlib import Path

from manual_test_coverage.core.module_loader import ModuleLoader


class ModuleRegistry:
    """Load and expose function metadata for configured native modules."""

    def __init__(self, function_infos_dir: Path, loader=None):
        self._loader = loader or ModuleLoader(function_infos_dir)
        self._function_infos = {}
        self._offsets = {}

    @property
    def function_infos(self):
        """Return loaded function metadata by module name."""
        return self._function_infos

    @property
    def offsets(self):
        """Return loaded function offsets by module name."""
        return self._offsets

    def load_all(self, modules):
        """Load metadata for a list of modules."""
        for module in modules:
            self.load(module.name)

    def load(self, module_name):
        """Load metadata for one module."""
        try:
            function_infos, offsets = self._loader.load(module_name)
        except FileNotFoundError:
            logging.info("Function info file not found for %s", module_name)
            return

        self._function_infos[module_name] = function_infos
        self._offsets[module_name] = offsets
