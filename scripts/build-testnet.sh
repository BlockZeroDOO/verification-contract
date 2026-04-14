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
    contracts=("verification" "dfs")
fi

echo "Using compiler: ${compiler}"
"${compiler}" --version || true

build_contract() {
    local contract_name="$1"
    local source_file="src/${contract_name}.cpp"
    local dist_dir="${project_root}/dist/${contract_name}"
    local wasm_file="${dist_dir}/${contract_name}.wasm"
    local abi_file="${dist_dir}/${contract_name}.abi"

    if [[ ! -f "${project_root}/${source_file}" ]]; then
        echo "Source file not found for contract '${contract_name}': ${source_file}" >&2
        exit 1
    fi

    mkdir -p "${dist_dir}"

    echo "Building contract: ${contract_name}"

    pushd "${project_root}" >/dev/null
    "${compiler}" \
        -I "${include_dir}" \
        -O3 \
        --abigen \
        --abigen_output "${abi_file}" \
        "${source_file}" \
        -o "${wasm_file}"
    popd >/dev/null

    if [[ ! -f "${wasm_file}" ]]; then
        echo "Expected WASM artifact was not generated: ${wasm_file}" >&2
        exit 1
    fi

    if [[ ! -f "${abi_file}" ]]; then
        echo "Expected ABI artifact was not generated: ${abi_file}" >&2
        exit 1
    fi

    echo "Build completed:"
    echo "  Contract: ${contract_name}"
    echo "  WASM: ${wasm_file}"
    echo "  ABI : ${abi_file}"
}

for contract_name in "${contracts[@]}"; do
    build_contract "${contract_name}"
done
