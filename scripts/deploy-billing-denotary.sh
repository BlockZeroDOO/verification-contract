#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

RPC_URL="${RPC_URL:-https://history.denotary.io}"
DENOTARY_CHAIN_ID="${DENOTARY_CHAIN_ID:-9714ab662f0899c3ac4c5a02220f3d7ab61aacae311974239cc75f22c999cc48}"
BILLING_ACCOUNT="${BILLING_ACCOUNT:-verifbill}"
BUILD_BEFORE_DEPLOY="${BUILD_BEFORE_DEPLOY:-true}"

if ! command -v cleos >/dev/null 2>&1; then
    echo "cleos is required for deploy-billing-denotary.sh" >&2
    exit 1
fi

if [[ ${#BILLING_ACCOUNT} -gt 12 ]]; then
    echo "BILLING_ACCOUNT must be 12 characters or fewer for Antelope account names: ${BILLING_ACCOUNT}" >&2
    exit 1
fi

if [[ "${BUILD_BEFORE_DEPLOY}" == "true" ]]; then
    "${SCRIPT_DIR}/build-billing.sh"
fi

echo "[deploy-billing-denotary] Verifying billing chain account"
cleos -u "${RPC_URL}" get account "${BILLING_ACCOUNT}" >/dev/null

echo "[deploy-billing-denotary] Deploying verifbill to ${BILLING_ACCOUNT}"
cleos -u "${RPC_URL}" set contract "${BILLING_ACCOUNT}" "${PROJECT_ROOT}/dist/verifbill" -p "${BILLING_ACCOUNT}@active"

echo
echo "deNotary billing deploy completed."
echo
echo "RPC URL: ${RPC_URL}"
echo "chain id: ${DENOTARY_CHAIN_ID}"
echo "billing account: ${BILLING_ACCOUNT}"
