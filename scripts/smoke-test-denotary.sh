#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export RPC_URL="${RPC_URL:-https://history.denotary.io}"
export OWNER_ACCOUNT="${OWNER_ACCOUNT:-verifent}"
export VERIFICATION_ACCOUNT="${VERIFICATION_ACCOUNT:-verifent}"
export PAYMENT_TOKEN_CONTRACT="${PAYMENT_TOKEN_CONTRACT:-eosio.token}"
export PAYMENT_PRICE="${PAYMENT_PRICE:-1.0000 EOS}"

bash "${script_dir}/smoke-test.sh"
