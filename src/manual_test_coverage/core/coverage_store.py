"""Normalized native coverage storage and helpers."""

from collections import defaultdict


class CoverageStore:
    """Store covered offsets per module and expose a normalized view."""

    def __init__(self):
        self._covered_offsets = defaultdict(set)

    def add(self, module_name, offsets):
        """Record covered offsets for a module."""
        for offset in offsets:
            self._covered_offsets[module_name].add(int(offset))

    def clear(self):
        """Clear all recorded coverage data."""
        self._covered_offsets.clear()

    def as_dict(self):
        """Return a normalized, JSON-serializable view of the stored coverage."""
        return {
            module_name: sorted(offsets)
            for module_name, offsets in self._covered_offsets.items()
        }

    def for_module(self, module_name):
        """Return the stored offsets for a specific module."""
        return sorted(self._covered_offsets.get(module_name, set()))


def collect_covered_offsets(modules_covered):
    """Normalize Frida coverage payloads into a simple mapping."""
    store = CoverageStore()
    for module_name, function_offsets in modules_covered.items():
        store.add(module_name, function_offsets)
    return store.as_dict()
