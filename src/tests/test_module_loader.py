from pathlib import Path

from manual_test_coverage.core.module_loader import ModuleLoader


def test_module_loader_loads_function_infos_and_offsets(tmp_path: Path):
    info_dir = tmp_path / "info"
    info_dir.mkdir()
    (info_dir / "demo.exe.info").write_text(
        "func_a\tdemo.exe\tdemo.cpp\t10\n"
        "func_b\tdemo.exe\tdemo.cpp\t20\n"
        "broken\n",
        encoding="utf-8",
    )

    loader = ModuleLoader(info_dir)

    function_infos, offsets = loader.load("demo.exe")

    assert len(function_infos) == 2
    assert function_infos[0].name == "func_a"
    assert function_infos[1].address_offset == 20
    assert offsets == [10, 20]
