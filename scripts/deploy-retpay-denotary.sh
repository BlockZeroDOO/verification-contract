#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

RPC_URL="${RPC_URL:-https://history.denotary.io}"
DENOTARY_CHAIN_ID="${DENOTARY_CHAIN_ID:-9714ab662f0899c3ac4c5a02220f3d7ab61aacae311974239cc75f22c999cc48}"
RETPAY_ACCOUNT="${RETPAY_ACCOUNT:-verifretpay}"
BUILD_BEFORE_DEPLOY="${BUILD_BEFORE_DEPLOY:-true}"

if ! command -v cleos >/dev/null 2>&1; then
    echo "cleos is required for deploy-retpay-denotary.sh" >&2
    exit 1
fi

if [[ ${#RETPAY_ACCOUNT} -gt 12 ]]; then
    echo "RETPAY_ACCOUNT must be 12 characters or fewer for Antelope account names: ${RETPAY_ACCOUNT}" >&2
    exit 1
fi

if [[ "${BUILD_BEFORE_DEPLOY}" == "true" ]]; then
    "${SCRIPT_DIR}/build-retpay.sh"
fi

echo "[deploy-retpay-denotary] Verifying retail payment chain account"
cleos -u "${RPC_URL}" get account "${RETPAY_ACCOUNT}" >/dev/null

echo "[deploy-retpay-denotary] Deploying verifretpay to ${RETPAY_ACCOUNT}"
cleos -u "${RPC_URL}" set contract "${RETPAY_ACCOUNT}" "${PROJECT_ROOT}/dist/verifretpay" -p "${RETPAY_ACCOUNT}@active"

echo
echo "deNotary retail payment deploy completed."
echo
echo "RPC URL: ${RPC_URL}"
echo "chain id: ${DENOTARY_CHAIN_ID}"
echo "retail payment account: ${RETPAY_ACCOUNT}"
