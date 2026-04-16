#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

RPC_URL="${RPC_URL:-https://history.denotary.io}"
DENOTARY_CHAIN_ID="${DENOTARY_CHAIN_ID:-9714ab662f0899c3ac4c5a02220f3d7ab61aacae311974239cc75f22c999cc48}"
RETAIL_ACCOUNT="${RETAIL_ACCOUNT:-verifretail}"
BUILD_BEFORE_DEPLOY="${BUILD_BEFORE_DEPLOY:-true}"

if ! command -v cleos >/dev/null 2>&1; then
    echo "cleos is required for deploy-retail-denotary.sh" >&2
    exit 1
fi

if [[ ${#RETAIL_ACCOUNT} -gt 12 ]]; then
    echo "RETAIL_ACCOUNT must be 12 characters or fewer for Antelope account names: ${RETAIL_ACCOUNT}" >&2
    exit 1
fi

if [[ "${BUILD_BEFORE_DEPLOY}" == "true" ]]; then
    "${SCRIPT_DIR}/build-retail.sh"
fi

echo "[deploy-retail-denotary] WARNING: verifretail is a legacy contract and not part of the supported architecture."
echo "[deploy-retail-denotary] Supported retail model: verif + verifretpay."

echo "[deploy-retail-denotary] Verifying retail chain account"
cleos -u "${RPC_URL}" get account "${RETAIL_ACCOUNT}" >/dev/null

echo "[deploy-retail-denotary] Deploying verifretail to ${RETAIL_ACCOUNT}"
cleos -u "${RPC_URL}" set contract "${RETAIL_ACCOUNT}" "${PROJECT_ROOT}/dist/verifretail" -p "${RETAIL_ACCOUNT}@active"

echo
echo "deNotary retail deploy completed."
echo
echo "RPC URL: ${RPC_URL}"
echo "chain id: ${DENOTARY_CHAIN_ID}"
echo "retail account: ${RETAIL_ACCOUNT}"
