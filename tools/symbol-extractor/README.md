# Symbol Extractor

Native companion tool for generating function information consumed by
`manual-test-coverage`.

The core command-line flow, `.info` writer, and LLVM-backed Windows/PDB backend
are implemented. The PDB backend reads PE/COFF modules, resolves a matching PDB,
extracts source-backed function symbols, and writes the existing `.info` files
used by the Python runner.

## Build

```bash
cmake -S tools/symbol-extractor -B build/symbol-extractor -DCMAKE_BUILD_TYPE=Release
cmake --build build/symbol-extractor --config Release
ctest --test-dir build/symbol-extractor --output-on-failure
```

LLVM/PDB support is enabled by default. To build only the core without the PDB
backend:

```bash
cmake -S tools/symbol-extractor -B build/symbol-extractor -DSYMBOL_EXTRACTOR_ENABLE_LLVM_PDB=OFF
```

## CLI

```bash
symbol-extractor --module /path/to/module --output-dir /path/to/function_infos
symbol-extractor --module /path/to/module --pdb /path/to/module.pdb --output-dir /path/to/function_infos
```

Without `--pdb`, the backend resolves the PDB path from the PE CodeView debug
record. With `--pdb`, the supplied PDB is still checked against the module's
CodeView GUID and age when that information is present.

Generated files use the existing Python runner schema:

```text
function_name<TAB>module_name<TAB>source_file<TAB>address_offset
```

Exit codes:

```text
0  success
1  extraction or writer failure
2  invalid command-line usage
```
