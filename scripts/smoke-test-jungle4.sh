#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

export RPC_URL="${RPC_URL:-https://jungle4.api.eosnation.io}"
export OWNER_ACCOUNT="${OWNER_ACCOUNT:-managementel}"
export MANAGEMENT_ACCOUNT="${MANAGEMENT_ACCOUNT:-managementel}"
export VERIFICATION_ACCOUNT="${VERIFICATION_ACCOUNT:-verification}"
export PAYMENT_TOKEN_CONTRACT="${PAYMENT_TOKEN_CONTRACT:-eosio.token}"
export RETAIL_PRICE="${RETAIL_PRICE:-1.0000 JUNGLE}"
export WHOLESALE_PRICE="${WHOLESALE_PRICE:-0.1000 JUNGLE}"
export FREE_ENABLED="${FREE_ENABLED:-true}"
export FREE_DAILY_LIMIT="${FREE_DAILY_LIMIT:-100}"

bash "${script_dir}/smoke-test.sh"
