# Local Packaging

Build on the target OS. PyInstaller does not cross-compile.

macOS/Linux:

```bash
./packaging/build-local.sh
```

Windows PowerShell:

```powershell
.\packaging\build-local.ps1
```

The package is written to:

```text
dist/manual-test-coverage
```

The scripts install PyInstaller into the Poetry environment if it is missing.

The local package build also builds the native symbol extractor with CMake and
copies it into:

```text
dist/manual-test-coverage/tools/symbol-extractor
```

The default symbol extractor build requires LLVM development files for the
Windows/PDB backend. To build only the extractor core, configure CMake with:

```text
-DSYMBOL_EXTRACTOR_ENABLE_LLVM_PDB=OFF
```
