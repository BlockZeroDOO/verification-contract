#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export RPC_URL="${RPC_URL:-https://jungle4.api.eosnation.io}"
export READ_RPC_URL="${READ_RPC_URL:-https://jungle4.cryptolions.io}"
export BILLING_ACCOUNT="${BILLING_ACCOUNT:-vadim1111111}"
export OWNER_ACCOUNT="${OWNER_ACCOUNT:-vadim1111111}"
export VERIFICATION_ACCOUNT="${VERIFICATION_ACCOUNT:-decentrfstor}"
export RETAIL_PAYMENT_ACCOUNT="${RETAIL_PAYMENT_ACCOUNT:-verification}"
export PAYER_ACCOUNT="${PAYER_ACCOUNT:-verification}"
export SUBMITTER_ACCOUNT="${SUBMITTER_ACCOUNT:-verification}"
export SCHEMA_ID="${SCHEMA_ID:-1776342316}"
export POLICY_SINGLE_ID="${POLICY_SINGLE_ID:-1776343316}"
export POLICY_BATCH_ID="${POLICY_BATCH_ID:-1776343317}"
export WAIT_TIMEOUT_SEC="${WAIT_TIMEOUT_SEC:-90}"

"${script_dir}/smoke-test-billing.sh"
