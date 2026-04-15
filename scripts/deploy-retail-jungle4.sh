#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

RPC_URL="${RPC_URL:-https://jungle4.api.eosnation.io}"
EXPECTED_CHAIN_ID="${EXPECTED_CHAIN_ID:-73e4385a2708e6d7048834fbc1079f2fabb17b3c125b146af438971e90716c4d}"
RETAIL_ACCOUNT="${RETAIL_ACCOUNT:-verifretail}"
BUILD_BEFORE_DEPLOY="${BUILD_BEFORE_DEPLOY:-true}"

if ! command -v cleos >/dev/null 2>&1; then
    echo "cleos is required for deploy-retail-jungle4.sh" >&2
    exit 1
fi

if [[ ${#RETAIL_ACCOUNT} -gt 12 ]]; then
    echo "RETAIL_ACCOUNT must be 12 characters or fewer for Antelope account names: ${RETAIL_ACCOUNT}" >&2
    exit 1
fi

if [[ "${BUILD_BEFORE_DEPLOY}" == "true" ]]; then
    "${SCRIPT_DIR}/build-retail.sh"
fi

echo "[deploy-retail-jungle4] Verifying retail chain account"
cleos -u "${RPC_URL}" get account "${RETAIL_ACCOUNT}" >/dev/null

echo "[deploy-retail-jungle4] Deploying verifretail to ${RETAIL_ACCOUNT}"
cleos -u "${RPC_URL}" set contract "${RETAIL_ACCOUNT}" "${PROJECT_ROOT}/dist/verifretail" -p "${RETAIL_ACCOUNT}@active"

echo
echo "Jungle4 retail deploy completed."
echo
echo "RPC URL: ${RPC_URL}"
echo "chain id: ${EXPECTED_CHAIN_ID}"
echo "retail account: ${RETAIL_ACCOUNT}"
