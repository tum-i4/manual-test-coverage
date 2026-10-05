# Manual Test Coverage

Record native function coverage during manual tests using Frida and a PyQt5 GUI,
then export Cobertura XML reports.

## Usage

Install Python 3.10–3.14 and Poetry, then install the project dependencies:

```bash
poetry install
```

Start the target application separately and attach to its PID:

```bash
poetry run python -m manual_test_coverage.main \
  --target /path/to/app \
  --function_infos /path/to/function_infos \
  --pid 1234
```

The function information directory must contain a `<module_name>.info` file for
each instrumented module. See the [symbol extractor guide](tools/symbol-extractor/README.md)
for the format and how to generate files from Windows PE/PDB symbols.

In the GUI, start a named test case, perform the manual test, then end the test
to save coverage. Reports default to `coverage_reports/`, grouped by tester ID
and timestamped test case, and are written when coverage is available.

CLI options:

| Option | Description |
| --- | --- |
| `--target PATH`, `-t PATH` | Required. Path to the target native executable. |
| `--function_infos PATH`, `-f PATH` | Required. Directory containing `.info` files with function offsets. |
| `--output_dir PATH`, `-o PATH` | Report directory. Default: `coverage_reports`. |
| `--included_modules REGEX`, `-i REGEX` | Select modules in the target executable's directory. Default: only the target executable. |
| `--pid PID`, `-p PID` | PID of the running target process to attach to. Default: `8123`. |
| `--agent_script PATH`, `--agent-script PATH` | Use a custom Frida agent. Default: the bundled agent for the current OS. |
| `--help`, `-h` | Show usage and exit. |

## Packaging

Build on the destination OS; PyInstaller does not cross-compile. In addition to
the Python dependencies, install CMake 3.20+, a C++17 compiler, and LLVM
development files for the symbol extractor's default PDB backend.

macOS/Linux:

```bash
./packaging/build-local.sh
```

Windows PowerShell:

```powershell
.\packaging\build-local.ps1
```

Distribute the entire `dist/manual-test-coverage/` directory. It includes the
application, platform launcher, and `tools/symbol-extractor/` companion tool.
From that directory, run:

```bash
./run-coverage.sh --target /path/to/app --function_infos /path/to/info --pid 1234
```

```powershell
.\run-coverage.ps1 -Target C:\path\app.exe -FunctionInfos C:\path\info -Pid 1234
```

To build a Python wheel and source archive instead, run `poetry build`;
these are written to `dist/` and require Python and the declared dependencies.
See [packaging notes](packaging/BUILDING.md) for more details.
