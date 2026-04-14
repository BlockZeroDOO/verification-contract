#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(cd "${script_dir}/.." && pwd)"

RPC_URL="${RPC_URL:-https://history.denotary.io}"
DENOTARY_CHAIN_ID="${DENOTARY_CHAIN_ID:-9714ab662f0899c3ac4c5a02220f3d7ab61aacae311974239cc75f22c999cc48}"
VERIFICATION_ACCOUNT="${VERIFICATION_ACCOUNT:-verification}"
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
        echo "This codebase expects the verification contract account to be exactly 'verification'." >&2
        echo "Deploy to 'verification' or patch the hardcoded contract name first." >&2
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

        if [[ "${chain_id}" != "${DENOTARY_CHAIN_ID}" ]]; then
            echo "RPC_URL does not appear to be the deNotary chain." >&2
            echo "Expected chain id: ${DENOTARY_CHAIN_ID}" >&2
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

    echo "[deploy-denotary] Deploying ${contract_name} to ${account_name}"
    cleos -u "${RPC_URL}" set contract "${account_name}" "${dist_dir}" -p "${account_name}@active"
}

add_code_permission() {
    local account_name="$1"

    echo "[deploy-denotary] Enabling eosio.code on ${account_name}@active"
    cleos -u "${RPC_URL}" set account permission "${account_name}" active --add-code -p "${account_name}@active"
}

require_command cleos
require_account_name_constraints
check_chain

if [[ "${BUILD_BEFORE_DEPLOY}" == "true" ]]; then
    echo "[deploy-denotary] Building contract artifacts"
    if [[ "${DEPLOY_DFS}" == "true" ]]; then
        bash "${project_root}/scripts/build-testnet.sh" verification dfs
    else
        bash "${project_root}/scripts/build-testnet.sh" verification
    fi
fi

require_artifact verification

if [[ "${DEPLOY_DFS}" == "true" ]]; then
    require_artifact dfs
fi

echo "[deploy-denotary] Verifying chain accounts"
require_chain_account "${VERIFICATION_ACCOUNT}"
if [[ "${DEPLOY_DFS}" == "true" ]]; then
    require_chain_account "${DFS_ACCOUNT}"
fi

deploy_contract "${VERIFICATION_ACCOUNT}" verification
add_code_permission "${VERIFICATION_ACCOUNT}"

if [[ "${DEPLOY_DFS}" == "true" ]]; then
    deploy_contract "${DFS_ACCOUNT}" dfs
    add_code_permission "${DFS_ACCOUNT}"
fi

cat <<EOF

deNotary deploy completed.

RPC URL: ${RPC_URL}
chain id: ${DENOTARY_CHAIN_ID}
verification account: ${VERIFICATION_ACCOUNT}
dfs account: ${DFS_ACCOUNT}
dfs deployed: ${DEPLOY_DFS}

Next steps:
  - Configure verification payment tokens with setpaytoken.
  - Optionally bootstrap dfs policy and accepted tokens.
  - Verify tables with cleos get table commands from README.md

EOF
