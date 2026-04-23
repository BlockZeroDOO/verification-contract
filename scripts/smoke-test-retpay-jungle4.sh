#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export RPC_URL="${RPC_URL:-https://jungle4.api.eosnation.io}"
export READ_RPC_URL="${READ_RPC_URL:-https://jungle4.cryptolions.io}"
export OWNER_ACCOUNT="${OWNER_ACCOUNT:-verification}"
export VERIFICATION_ACCOUNT="${VERIFICATION_ACCOUNT:-decentrfstor}"
export VERIFICATION_BILLING_ACCOUNT="${VERIFICATION_BILLING_ACCOUNT:-vadim1111111}"
export SUBMITTER_ACCOUNT="${SUBMITTER_ACCOUNT:-decentrfstor}"
export SCHEMA_ID="${SCHEMA_ID:-1776342316}"
export POLICY_SINGLE_ID="${POLICY_SINGLE_ID:-1776343316}"
export POLICY_BATCH_ID="${POLICY_BATCH_ID:-1776343317}"
export WAIT_TIMEOUT_SEC="${WAIT_TIMEOUT_SEC:-90}"

if [[ -z "${RETPAY_ACCOUNT:-}" ]]; then
    export RETPAY_ACCOUNT="verification"
fi

"${SCRIPT_DIR}/smoke-test-retpay.sh"
