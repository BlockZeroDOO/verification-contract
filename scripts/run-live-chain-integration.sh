#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(cd "${script_dir}/.." && pwd)"

if [[ -x "${project_root}/.venv/bin/python" ]]; then
    python_cmd="${project_root}/.venv/bin/python"
elif command -v python3 >/dev/null 2>&1; then
    python_cmd="python3"
elif command -v python >/dev/null 2>&1; then
    python_cmd="python"
elif [[ -x "${project_root}/.venv/Scripts/python.exe" ]]; then
    python_cmd="${project_root}/.venv/Scripts/python.exe"
else
    echo "Python interpreter not found." >&2
    exit 1
fi

cd "${project_root}"
"${python_cmd}" tests/live_chain_integration.py "$@"
