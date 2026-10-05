#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
PLATFORM_NAME="${1:-$(uname -s)}"
SYMBOL_EXTRACTOR_BUILD_DIR="${PROJECT_ROOT}/build/symbol-extractor"
SYMBOL_EXTRACTOR_INSTALL_DIR="${SYMBOL_EXTRACTOR_BUILD_DIR}/install"

case "${PLATFORM_NAME}" in
    Windows|windows)
        LAUNCHER="${PROJECT_ROOT}/packaging/windows/run-coverage.ps1"
        ;;
    Darwin|darwin|macos|macOS)
        LAUNCHER="${PROJECT_ROOT}/packaging/macos/run-coverage.sh"
        ;;
    Linux|linux)
        LAUNCHER="${PROJECT_ROOT}/packaging/linux/run-coverage.sh"
        ;;
    *)
        echo "Unsupported platform for this script: ${PLATFORM_NAME}" >&2
        exit 1
        ;;
esac

cd "${PROJECT_ROOT}"

cmake -S tools/symbol-extractor \
    -B "${SYMBOL_EXTRACTOR_BUILD_DIR}" \
    -DCMAKE_BUILD_TYPE=Release \
    -DCMAKE_INSTALL_PREFIX="${SYMBOL_EXTRACTOR_INSTALL_DIR}"
cmake --build "${SYMBOL_EXTRACTOR_BUILD_DIR}" --config Release
cmake --install "${SYMBOL_EXTRACTOR_BUILD_DIR}" --config Release

poetry run python -m pip show pyinstaller >/dev/null 2>&1 || \
    poetry run python -m pip install pyinstaller

poetry run pyinstaller packaging/manual-test-coverage.spec --clean --noconfirm

cp "${LAUNCHER}" dist/manual-test-coverage/
cp packaging/README.txt dist/manual-test-coverage/
mkdir -p dist/manual-test-coverage/tools
cp -R "${SYMBOL_EXTRACTOR_INSTALL_DIR}/tools/symbol-extractor" \
    dist/manual-test-coverage/tools/

if [[ "${PLATFORM_NAME}" != "Windows" && "${PLATFORM_NAME}" != "windows" ]]; then
    chmod +x dist/manual-test-coverage/run-coverage.sh
    chmod +x dist/manual-test-coverage/manual-test-coverage
    chmod +x dist/manual-test-coverage/tools/symbol-extractor/symbol-extractor
fi

echo "Package created at dist/manual-test-coverage"
