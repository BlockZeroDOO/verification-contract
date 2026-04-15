#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export RPC_URL="${RPC_URL:-https://history.denotary.io}"

if [[ -z "${RETAIL_ACCOUNT:-}" ]]; then
    export RETAIL_ACCOUNT="verifretail"
fi

"${SCRIPT_DIR}/smoke-test-retail.sh"
