"""Helper to load native module metadata from .info files."""

from dataclasses import dataclass
from pathlib import Path

FUNCTION_INFO_EXT = ".info"
SEPARATOR = "\t"


@dataclass
class FunctionInfo:
    """Describe a function available for native coverage instrumentation."""

    name: str
    module_name: str
    source_file: str
    address_offset: int

    @classmethod
    def from_line(cls, line: str):
        """Build a FunctionInfo instance from one line in an .info file."""
        name, module_name, source_file, address_offset = line.strip().split(SEPARATOR)
        return cls(name, module_name, source_file, int(address_offset))


class ModuleLoader:
    """Load native module metadata and offsets for coverage instrumentation."""

    def __init__(self, function_infos_dir: Path):
        self._function_infos_dir = Path(function_infos_dir)

    def load(self, module_name: str):
        """Return function metadata and offsets for one native module."""
        info_file = self._function_infos_dir / f"{module_name}{FUNCTION_INFO_EXT}"
        with info_file.open("r", encoding="utf-8") as fp:
            function_infos = []
            offsets = []
            for line in fp:
                try:
                    function_info = FunctionInfo.from_line(line)
                    function_infos.append(function_info)
                    offsets.append(function_info.address_offset)
                except ValueError:
                    continue

        return function_infos, offsets
