from pathlib import Path

from manual_test_coverage.core.module_registry import ModuleRegistry


def test_module_registry_loads_offsets_and_function_infos(tmp_path: Path):
    info_dir = tmp_path / "info"
    info_dir.mkdir()
    (info_dir / "demo.exe.info").write_text(
        "func_a\tdemo.exe\tdemo.cpp\t10\n"
        "func_b\tdemo.exe\tdemo.cpp\t20\n",
        encoding="utf-8",
    )
    registry = ModuleRegistry(
        function_infos_dir=info_dir,
    )

    registry.load("demo.exe")

    assert [info.name for info in registry.function_infos["demo.exe"]] == [
        "func_a",
        "func_b",
    ]
    assert registry.offsets == {"demo.exe": [10, 20]}


def test_module_registry_skips_missing_function_info(tmp_path: Path):
    registry = ModuleRegistry(
        function_infos_dir=tmp_path,
    )

    registry.load("missing.exe")

    assert registry.function_infos == {}
    assert registry.offsets == {}
