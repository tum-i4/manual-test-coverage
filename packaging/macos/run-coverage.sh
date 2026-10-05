#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TOOL_PATH="${SCRIPT_DIR}/manual-test-coverage"

exec "${TOOL_PATH}" "$@"
