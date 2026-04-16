#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export RPC_URL="${RPC_URL:-https://history.denotary.io}"
export READ_RPC_URL="${READ_RPC_URL:-${RPC_URL}}"

if [[ -z "${RETPAY_ACCOUNT:-}" ]]; then
    export RETPAY_ACCOUNT="verifretpay"
fi

"${SCRIPT_DIR}/smoke-test-retpay.sh"
