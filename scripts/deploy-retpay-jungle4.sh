#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

RPC_URL="${RPC_URL:-https://jungle4.api.eosnation.io}"
EXPECTED_CHAIN_ID="${EXPECTED_CHAIN_ID:-73e4385a2708e6d7048834fbc1079f2fabb17b3c125b146af438971e90716c4d}"
RETPAY_ACCOUNT="${RETPAY_ACCOUNT:-verifretpay}"
BUILD_BEFORE_DEPLOY="${BUILD_BEFORE_DEPLOY:-true}"

if ! command -v cleos >/dev/null 2>&1; then
    echo "cleos is required for deploy-retpay-jungle4.sh" >&2
    exit 1
fi

if [[ ${#RETPAY_ACCOUNT} -gt 12 ]]; then
    echo "RETPAY_ACCOUNT must be 12 characters or fewer for Antelope account names: ${RETPAY_ACCOUNT}" >&2
    exit 1
fi

if [[ "${BUILD_BEFORE_DEPLOY}" == "true" ]]; then
    "${SCRIPT_DIR}/build-retpay.sh"
fi

echo "[deploy-retpay-jungle4] Verifying retail payment chain account"
cleos -u "${RPC_URL}" get account "${RETPAY_ACCOUNT}" >/dev/null

echo "[deploy-retpay-jungle4] Deploying verifretpay to ${RETPAY_ACCOUNT}"
cleos -u "${RPC_URL}" set contract "${RETPAY_ACCOUNT}" "${PROJECT_ROOT}/dist/verifretpay" -p "${RETPAY_ACCOUNT}@active"

echo
echo "Jungle4 retail payment deploy completed."
echo
echo "RPC URL: ${RPC_URL}"
echo "chain id: ${EXPECTED_CHAIN_ID}"
echo "retail payment account: ${RETPAY_ACCOUNT}"
