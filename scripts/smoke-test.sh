#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export RPC_URL="${RPC_URL:-https://history.denotary.io}"
export OWNER_ACCOUNT="${OWNER_ACCOUNT:?Set OWNER_ACCOUNT to the enterprise governance account.}"
export VERIFICATION_ACCOUNT="${VERIFICATION_ACCOUNT:-verifent}"
export SUBMITTER_ACCOUNT="${SUBMITTER_ACCOUNT:-${PAYER_ACCOUNT:-}}"

if [[ -z "${SUBMITTER_ACCOUNT}" ]]; then
    echo "Set SUBMITTER_ACCOUNT (or legacy PAYER_ACCOUNT) before running smoke-test.sh" >&2
    exit 1
fi

printf '[smoke-test] Delegating to smoke-test-onchain.sh\n'
exec bash "${script_dir}/smoke-test-onchain.sh"
