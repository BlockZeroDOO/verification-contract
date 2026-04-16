#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(cd "${script_dir}/.." && pwd)"

RPC_URL="${RPC_URL:-https://jungle4.api.eosnation.io}"
JUNGLE4_CHAIN_ID="${JUNGLE4_CHAIN_ID:-73e4385a2708e6d7048834fbc1079f2fabb17b3c125b146af438971e90716c4d}"
VERIFICATION_ACCOUNT="${VERIFICATION_ACCOUNT:-verif}"
BUILD_BEFORE_DEPLOY="${BUILD_BEFORE_DEPLOY:-true}"

require_command() {
    local command_name="$1"
    if ! command -v "${command_name}" >/dev/null 2>&1; then
        echo "${command_name} is required but was not found in PATH." >&2
        exit 1
    fi
}

require_artifact() {
    local contract_name="$1"
    local dist_dir="${project_root}/dist/${contract_name}"

    if [[ ! -f "${dist_dir}/${contract_name}.wasm" ]]; then
        echo "Missing artifact: ${dist_dir}/${contract_name}.wasm" >&2
        exit 1
    fi

    if [[ ! -f "${dist_dir}/${contract_name}.abi" ]]; then
        echo "Missing artifact: ${dist_dir}/${contract_name}.abi" >&2
        exit 1
    fi
}

check_chain() {
    local chain_id

    if command -v curl >/dev/null 2>&1 && command -v jq >/dev/null 2>&1; then
        chain_id="$(
            curl -fsSL -X POST "${RPC_URL}/v1/chain/get_info" \
                -H 'Content-Type: application/json' \
                -d '{}' \
                | jq -r '.chain_id'
        )"

        if [[ "${chain_id}" != "${JUNGLE4_CHAIN_ID}" ]]; then
            echo "RPC_URL does not appear to be Jungle4." >&2
            echo "Expected chain id: ${JUNGLE4_CHAIN_ID}" >&2
            echo "Actual chain id:   ${chain_id}" >&2
            exit 1
        fi
    fi
}

require_chain_account() {
    local account_name="$1"
    cleos -u "${RPC_URL}" get account "${account_name}" >/dev/null
}

deploy_contract() {
    local account_name="$1"
    local contract_name="$2"
    local dist_dir="${project_root}/dist/${contract_name}"

    echo "[deploy-jungle4] Deploying ${contract_name} to ${account_name}"
    cleos -u "${RPC_URL}" set contract "${account_name}" "${dist_dir}" -p "${account_name}@active"
}

add_code_permission() {
    local account_name="$1"

    echo "[deploy-jungle4] Enabling eosio.code on ${account_name}@active"
    cleos -u "${RPC_URL}" set account permission "${account_name}" active --add-code -p "${account_name}@active"
}

require_command cleos
check_chain

if [[ "${BUILD_BEFORE_DEPLOY}" == "true" ]]; then
    echo "[deploy-jungle4] Building contract artifacts"
    bash "${project_root}/scripts/build-testnet.sh" verif
fi

require_artifact verif

echo "[deploy-jungle4] Verifying chain accounts"
require_chain_account "${VERIFICATION_ACCOUNT}"

deploy_contract "${VERIFICATION_ACCOUNT}" verif

cat <<EOF

Jungle4 deploy completed.

RPC URL: ${RPC_URL}
chain id: ${JUNGLE4_CHAIN_ID}
verification account: ${VERIFICATION_ACCOUNT}

Next steps:
  - Run the on-chain smoke test against Jungle4.
  - If you need the DFS contract, deploy it from C:\projects\decentralized_storage\contracts\dfs

EOF
