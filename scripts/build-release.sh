#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(cd "${script_dir}/.." && pwd)"
include_dir="${project_root}/include"

if command -v cdt-cpp >/dev/null 2>&1; then
    compiler="cdt-cpp"
elif command -v eosio-cpp >/dev/null 2>&1; then
    compiler="eosio-cpp"
else
    echo "Neither cdt-cpp nor eosio-cpp is installed or available in PATH." >&2
    exit 1
fi

if [[ $# -gt 0 ]]; then
    contracts=("$@")
else
    contracts=("verification" "managementel" "dfs")
fi

build_contract() {
    local contract_name="$1"
    local source_file="src/${contract_name}.cpp"
    local dist_dir="${project_root}/dist/${contract_name}"
    local wasm_file="${dist_dir}/${contract_name}.wasm"
    local abi_file="${dist_dir}/${contract_name}.abi"
    local checksums_created="no"

    if [[ ! -f "${project_root}/${source_file}" ]]; then
        echo "Source file not found for contract '${contract_name}': ${source_file}" >&2
        exit 1
    fi

    mkdir -p "${dist_dir}"

    pushd "${project_root}" >/dev/null
    "${compiler}" \
        -I "${include_dir}" \
        -O3 \
        --abigen \
        "${source_file}" \
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
    fi

    echo "Release build completed:"
    echo "  Contract: ${contract_name}"
    echo "  WASM: ${wasm_file}"
    echo "  ABI : ${abi_file}"
    if [[ "${checksums_created}" == "yes" ]]; then
        echo "  SHA256: ${wasm_file}.sha256"
        echo "  SHA256: ${abi_file}.sha256"
    fi
}

for contract_name in "${contracts[@]}"; do
    build_contract "${contract_name}"
done
