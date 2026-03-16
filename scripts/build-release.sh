#!/usr/bin/env bash

set -euo pipefail

contract_name="${1:-verification}"
script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(cd "${script_dir}/.." && pwd)"
source_file="${project_root}/src/verification.cpp"
include_dir="${project_root}/include"
dist_dir="${project_root}/dist/${contract_name}"
wasm_file="${dist_dir}/${contract_name}.wasm"
abi_file="${dist_dir}/${contract_name}.abi"

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
    "src/verification.cpp" \
    -o "${wasm_file}"
popd >/dev/null

if command -v sha256sum >/dev/null 2>&1; then
    sha256sum "${wasm_file}" > "${wasm_file}.sha256"
    sha256sum "${abi_file}" > "${abi_file}.sha256"
    checksums_created="yes"
elif command -v shasum >/dev/null 2>&1; then
    shasum -a 256 "${wasm_file}" > "${wasm_file}.sha256"
    shasum -a 256 "${abi_file}" > "${abi_file}.sha256"
    checksums_created="yes"
else
    checksums_created="no"
fi

echo "Release build completed:"
echo "  WASM: ${wasm_file}"
echo "  ABI : ${abi_file}"
if [[ "${checksums_created}" == "yes" ]]; then
    echo "  SHA256: ${wasm_file}.sha256"
    echo "  SHA256: ${abi_file}.sha256"
fi
