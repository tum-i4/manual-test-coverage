# -*- mode: python ; coding: utf-8 -*-

from pathlib import Path

PROJECT_ROOT = Path(SPECPATH).parents[0]
SRC_DIR = PROJECT_ROOT / "src"
AGENTS_DIR = SRC_DIR / "manual_test_coverage" / "agents"
PACKAGE_DIR = SRC_DIR / "manual_test_coverage"


a = Analysis(
    [str(SRC_DIR / "manual_test_coverage" / "main.py")],
    pathex=[str(SRC_DIR)],
    binaries=[],
    datas=[
        (str(AGENTS_DIR), "manual_test_coverage/agents"),
        (str(PACKAGE_DIR / "dialog_start.ui"), "manual_test_coverage"),
        (str(PACKAGE_DIR / "mainwindow.ui"), "manual_test_coverage"),
    ],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name="manual-test-coverage",
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
coll = COLLECT(
    exe,
    a.binaries,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name="manual-test-coverage",
)
