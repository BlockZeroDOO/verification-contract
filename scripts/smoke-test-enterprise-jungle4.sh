#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export RPC_URL="${RPC_URL:-https://jungle4.api.eosnation.io}"
export READ_RPC_URL="${READ_RPC_URL:-https://jungle4.cryptolions.io}"
export OWNER_ACCOUNT="${OWNER_ACCOUNT:-verifent}"
export VERIFICATION_ACCOUNT="${VERIFICATION_ACCOUNT:-verifent}"
export SUBMITTER_ACCOUNT="${SUBMITTER_ACCOUNT:-}"
export WAIT_TIMEOUT_SEC="${WAIT_TIMEOUT_SEC:-90}"

"${script_dir}/smoke-test-onchain.sh"
