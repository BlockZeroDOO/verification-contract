#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export RPC_URL="${RPC_URL:-https://history.denotary.io}"
export OWNER_ACCOUNT="${OWNER_ACCOUNT:-verifent}"
export VERIFICATION_ACCOUNT="${VERIFICATION_ACCOUNT:-verifent}"
export SUBMITTER_ACCOUNT="${SUBMITTER_ACCOUNT:-}"

"${script_dir}/smoke-test-onchain.sh"
