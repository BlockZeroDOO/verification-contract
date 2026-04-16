#!/usr/bin/env bash

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export RPC_URL="${RPC_URL:-https://jungle4.api.eosnation.io}"
export READ_RPC_URL="${READ_RPC_URL:-https://jungle4.cryptolions.io}"
export WAIT_TIMEOUT_SEC="${WAIT_TIMEOUT_SEC:-90}"

"${SCRIPT_DIR}/smoke-test-unified-retail.sh"
