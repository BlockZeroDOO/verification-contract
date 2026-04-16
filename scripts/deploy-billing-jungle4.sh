#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

RPC_URL="${RPC_URL:-https://jungle4.api.eosnation.io}"
EXPECTED_CHAIN_ID="${EXPECTED_CHAIN_ID:-73e4385a2708e6d7048834fbc1079f2fabb17b3c125b146af438971e90716c4d}"
BILLING_ACCOUNT="${BILLING_ACCOUNT:-verifbill}"
BUILD_BEFORE_DEPLOY="${BUILD_BEFORE_DEPLOY:-true}"

if ! command -v cleos >/dev/null 2>&1; then
    echo "cleos is required for deploy-billing-jungle4.sh" >&2
    exit 1
fi

if [[ ${#BILLING_ACCOUNT} -gt 12 ]]; then
    echo "BILLING_ACCOUNT must be 12 characters or fewer for Antelope account names: ${BILLING_ACCOUNT}" >&2
    exit 1
fi

if [[ "${BUILD_BEFORE_DEPLOY}" == "true" ]]; then
    "${SCRIPT_DIR}/build-billing.sh"
fi

echo "[deploy-billing-jungle4] Verifying billing chain account"
cleos -u "${RPC_URL}" get account "${BILLING_ACCOUNT}" >/dev/null

echo "[deploy-billing-jungle4] Deploying verifbill to ${BILLING_ACCOUNT}"
cleos -u "${RPC_URL}" set contract "${BILLING_ACCOUNT}" "${PROJECT_ROOT}/dist/verifbill" -p "${BILLING_ACCOUNT}@active"

echo
echo "Jungle4 billing deploy completed."
echo
echo "RPC URL: ${RPC_URL}"
echo "chain id: ${EXPECTED_CHAIN_ID}"
echo "billing account: ${BILLING_ACCOUNT}"
