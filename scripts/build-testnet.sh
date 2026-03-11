#!/usr/bin/env bash

set -euo pipefail

contract_name="${1:-gfnotary}"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(cd "${script_dir}/.." && pwd)"
source_file="${project_root}/src/gfnotary.cpp"
include_dir="${project_root}/include"
dist_dir="${project_root}/dist/${contract_name}"
wasm_file="${dist_dir}/${contract_name}.wasm"

if command -v cdt-cpp >/dev/null 2>&1; then
    compiler="cdt-cpp"
elif command -v eosio-cpp >/dev/null 2>&1; then
    compiler="eosio-cpp"
else
    echo "Neither cdt-cpp nor eosio-cpp is installed or available in PATH." >&2
    exit 1
fi

mkdir -p "${dist_dir}"

pushd "${project_root}" >/dev/null
"${compiler}" \
    -I "${include_dir}" \
    -O3 \
    --abigen \
    "src/gfnotary.cpp" \
    -o "${wasm_file}"
popd >/dev/null

echo "Build completed:"
echo "  WASM: ${wasm_file}"
echo "  ABI : ${dist_dir}/${contract_name}.abi"
