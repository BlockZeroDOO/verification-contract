#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export RPC_URL="${RPC_URL:-https://history.denotary.io}"
export OWNER_ACCOUNT="${OWNER_ACCOUNT:-verif}"
export VERIFICATION_ACCOUNT="${VERIFICATION_ACCOUNT:-verif}"
export BILLING_OWNER_ACCOUNT="${BILLING_OWNER_ACCOUNT:-${VERIFICATION_BILLING_ACCOUNT:-verifbill}}"
export VERIFICATION_BILLING_ACCOUNT="${VERIFICATION_BILLING_ACCOUNT:-verifbill}"
export SUBMITTER_ACCOUNT="${SUBMITTER_ACCOUNT:-${PAYER_ACCOUNT:-}}"

if [[ -z "${SUBMITTER_ACCOUNT}" ]]; then
    echo "Set SUBMITTER_ACCOUNT (or legacy PAYER_ACCOUNT) before running smoke-test-denotary.sh" >&2
    exit 1
fi

bash "${script_dir}/smoke-test-onchain.sh"
