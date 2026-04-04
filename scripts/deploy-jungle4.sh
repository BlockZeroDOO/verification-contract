#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(cd "${script_dir}/.." && pwd)"

RPC_URL="${RPC_URL:-https://jungle4.api.eosnation.io}"
JUNGLE4_CHAIN_ID="${JUNGLE4_CHAIN_ID:-73e4385a2708e6d7048834fbc1079f2fabb17b3c125b146af438971e90716c4d}"
VERIFICATION_ACCOUNT="${VERIFICATION_ACCOUNT:-verification}"
MANAGEMENT_ACCOUNT="${MANAGEMENT_ACCOUNT:-managementel}"
DFS_ACCOUNT="${DFS_ACCOUNT:-dfs}"
DEPLOY_DFS="${DEPLOY_DFS:-true}"
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

require_account_name_constraints() {
    if [[ "${VERIFICATION_ACCOUNT}" != "verification" ]]; then
        echo "This codebase hardcodes verification writes to account 'verification'." >&2
        echo "Deploy verification to that exact Jungle4 account or patch the contract constants first." >&2
        exit 1
    fi

    if [[ "${MANAGEMENT_ACCOUNT}" != "managementel" ]]; then
        echo "This codebase hardcodes the authorized writer as account 'managementel'." >&2
        echo "Deploy management to that exact Jungle4 account or patch the contract constants first." >&2
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
require_account_name_constraints
check_chain

if [[ "${BUILD_BEFORE_DEPLOY}" == "true" ]]; then
    echo "[deploy-jungle4] Building contract artifacts"
    if [[ "${DEPLOY_DFS}" == "true" ]]; then
        bash "${project_root}/scripts/build-testnet.sh" verification managementel dfs
    else
        bash "${project_root}/scripts/build-testnet.sh" verification managementel
    fi
fi

require_artifact verification
require_artifact managementel

if [[ "${DEPLOY_DFS}" == "true" ]]; then
    require_artifact dfs
fi

echo "[deploy-jungle4] Verifying chain accounts"
require_chain_account "${VERIFICATION_ACCOUNT}"
require_chain_account "${MANAGEMENT_ACCOUNT}"
if [[ "${DEPLOY_DFS}" == "true" ]]; then
    require_chain_account "${DFS_ACCOUNT}"
fi

deploy_contract "${VERIFICATION_ACCOUNT}" verification
deploy_contract "${MANAGEMENT_ACCOUNT}" managementel
add_code_permission "${MANAGEMENT_ACCOUNT}"

if [[ "${DEPLOY_DFS}" == "true" ]]; then
    deploy_contract "${DFS_ACCOUNT}" dfs
    add_code_permission "${DFS_ACCOUNT}"
fi

cat <<EOF

Jungle4 deploy completed.

RPC URL: ${RPC_URL}
verification account: ${VERIFICATION_ACCOUNT}
management account: ${MANAGEMENT_ACCOUNT}
dfs account: ${DFS_ACCOUNT}
dfs deployed: ${DEPLOY_DFS}

Next steps:
  - Configure management payment tokens and free policy.
  - Optionally bootstrap dfs policy and accepted tokens.
  - Verify tables with cleos get table commands from docs/jungle4-deploy.md

EOF
