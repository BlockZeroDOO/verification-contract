#!/usr/bin/env bash

set -euo pipefail

RPC_URL="${RPC_URL:-https://dev-history.globalforce.io}"
CONTRACT_ACCOUNT="${CONTRACT_ACCOUNT:-globalnotary}"
PAYMENT_TOKEN_CONTRACT="${PAYMENT_TOKEN_CONTRACT:-eosio.token}"
PAYMENT_TOKEN_SYMBOL="${PAYMENT_TOKEN_SYMBOL:-4,GFT}"
RETAIL_PRICE="${RETAIL_PRICE:-1.0000 GFT}"
WHOLESALE_PRICE="${WHOLESALE_PRICE:-0.1000 GFT}"

: "${OWNER_ACCOUNT:?Set OWNER_ACCOUNT to the contract admin account.}"
: "${RETAIL_ACCOUNT:?Set RETAIL_ACCOUNT to a funded retail test account.}"
: "${WHOLESALE_ACCOUNT:?Set WHOLESALE_ACCOUNT to a funded wholesale test account.}"
: "${NONPROFIT_ACCOUNT:?Set NONPROFIT_ACCOUNT to a nonprofit test account.}"

if command -v jq >/dev/null 2>&1; then
    JQ_BIN="jq"
else
    echo "jq is required for smoke-test.sh" >&2
    exit 1
fi

if ! command -v cleos >/dev/null 2>&1; then
    echo "cleos is required for smoke-test.sh" >&2
    exit 1
fi

BASE_HASH="${BASE_HASH:-0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef}"
TIMESTAMP="$(date -u +%Y%m%d%H%M%S)"
WHOLESALE_REF="wh-${TIMESTAMP}"
RETAIL_REF="rt-${TIMESTAMP}"
NONPROFIT_REF="np-${TIMESTAMP}"
WHOLESALE_MEMO="${BASE_HASH}|SHA-256|none|${WHOLESALE_REF}"
RETAIL_MEMO="${BASE_HASH}|SHA-256|none|${RETAIL_REF}"

cleanup() {
    set +e
    cleos -u "${RPC_URL}" push action "${CONTRACT_ACCOUNT}" rmwhuser "[\"${WHOLESALE_ACCOUNT}\"]" -p "${OWNER_ACCOUNT}@active" >/dev/null 2>&1
    cleos -u "${RPC_URL}" push action "${CONTRACT_ACCOUNT}" rmnporg "[\"${NONPROFIT_ACCOUNT}\"]" -p "${OWNER_ACCOUNT}@active" >/dev/null 2>&1
}

trap cleanup EXIT

log() {
    printf '[smoke-test] %s\n' "$1"
}

get_table_json() {
    local table="$1"
    cleos -u "${RPC_URL}" get table "${CONTRACT_ACCOUNT}" "${CONTRACT_ACCOUNT}" "${table}"
}

count_rows() {
    local table="$1"
    get_table_json "${table}" | "${JQ_BIN}" '.rows | length'
}

assert_eq() {
    local expected="$1"
    local actual="$2"
    local message="$3"

    if [[ "${expected}" != "${actual}" ]]; then
        echo "Assertion failed: ${message}. Expected '${expected}', got '${actual}'." >&2
        exit 1
    fi
}

assert_contains_account() {
    local account="$1"
    local table_json="$2"
    local exists

    exists="$(printf '%s' "${table_json}" | "${JQ_BIN}" --arg account "${account}" 'any(.rows[]?; .account == $account)')"
    assert_eq "true" "${exists}" "account '${account}' should exist in wholesale table"
}

assert_proof_by_reference() {
    local reference="$1"
    local expected_submitter="$2"
    local expected_price="$3"
    local expected_wholesale="$4"

    local proofs_json proof_json submitter price wholesale_flag
    proofs_json="$(get_table_json proofs)"
    proof_json="$(printf '%s' "${proofs_json}" | "${JQ_BIN}" -c --arg ref "${reference}" '.rows[] | select(.client_reference == $ref)' | tail -n 1)"

    if [[ -z "${proof_json}" ]]; then
        echo "Assertion failed: proof with client_reference '${reference}' was not found." >&2
        exit 1
    fi

    submitter="$(printf '%s' "${proof_json}" | "${JQ_BIN}" -r '.submitter')"
    price="$(printf '%s' "${proof_json}" | "${JQ_BIN}" -r '.price_charged')"
    wholesale_flag="$(printf '%s' "${proof_json}" | "${JQ_BIN}" -r '.wholesale_pricing')"

    assert_eq "${expected_submitter}" "${submitter}" "submitter for reference '${reference}'"
    assert_eq "${expected_price}" "${price}" "price for reference '${reference}'"
    assert_eq "${expected_wholesale}" "${wholesale_flag}" "wholesale flag for reference '${reference}'"
}

log "Initial proof count"
INITIAL_PROOFS="$(count_rows proofs)"

log "Ensuring payment token config exists"
cleos -u "${RPC_URL}" push action "${CONTRACT_ACCOUNT}" setpaytoken "[\"${PAYMENT_TOKEN_CONTRACT}\",\"${RETAIL_PRICE}\",\"${WHOLESALE_PRICE}\"]" -p "${OWNER_ACCOUNT}@active"

log "Resetting wholesale test account state"
cleos -u "${RPC_URL}" push action "${CONTRACT_ACCOUNT}" rmwhuser "[\"${WHOLESALE_ACCOUNT}\"]" -p "${OWNER_ACCOUNT}@active" >/dev/null 2>&1 || true
cleos -u "${RPC_URL}" push action "${CONTRACT_ACCOUNT}" rmnporg "[\"${NONPROFIT_ACCOUNT}\"]" -p "${OWNER_ACCOUNT}@active" >/dev/null 2>&1 || true

log "Adding wholesale account ${WHOLESALE_ACCOUNT}"
cleos -u "${RPC_URL}" push action "${CONTRACT_ACCOUNT}" addwhuser "[\"${WHOLESALE_ACCOUNT}\",\"smoke test account\"]" -p "${OWNER_ACCOUNT}@active"

WHOLESALE_TABLE="$(get_table_json wholesale)"
assert_contains_account "${WHOLESALE_ACCOUNT}" "${WHOLESALE_TABLE}"

log "Submitting wholesale payment"
cleos -u "${RPC_URL}" push action "${PAYMENT_TOKEN_CONTRACT}" transfer "[\"${WHOLESALE_ACCOUNT}\",\"${CONTRACT_ACCOUNT}\",\"${WHOLESALE_PRICE}\",\"${WHOLESALE_MEMO}\"]" -p "${WHOLESALE_ACCOUNT}@active"
assert_proof_by_reference "${WHOLESALE_REF}" "${WHOLESALE_ACCOUNT}" "${WHOLESALE_PRICE}" "true"

log "Removing wholesale status"
cleos -u "${RPC_URL}" push action "${CONTRACT_ACCOUNT}" rmwhuser "[\"${WHOLESALE_ACCOUNT}\"]" -p "${OWNER_ACCOUNT}@active"

log "Submitting retail payment"
cleos -u "${RPC_URL}" push action "${PAYMENT_TOKEN_CONTRACT}" transfer "[\"${RETAIL_ACCOUNT}\",\"${CONTRACT_ACCOUNT}\",\"${RETAIL_PRICE}\",\"${RETAIL_MEMO}\"]" -p "${RETAIL_ACCOUNT}@active"
assert_proof_by_reference "${RETAIL_REF}" "${RETAIL_ACCOUNT}" "${RETAIL_PRICE}" "false"

log "Adding nonprofit account ${NONPROFIT_ACCOUNT}"
cleos -u "${RPC_URL}" push action "${CONTRACT_ACCOUNT}" addnporg "[\"${NONPROFIT_ACCOUNT}\",\"smoke test nonprofit\"]" -p "${OWNER_ACCOUNT}@active"

log "Submitting nonprofit proof without payment"
cleos -u "${RPC_URL}" push action "${CONTRACT_ACCOUNT}" submitfree "[\"${NONPROFIT_ACCOUNT}\",\"${BASE_HASH}\",\"SHA-256\",\"none\",\"${NONPROFIT_REF}\"]" -p "${NONPROFIT_ACCOUNT}@active"
assert_proof_by_reference "${NONPROFIT_REF}" "${NONPROFIT_ACCOUNT}" "0.0000 FREE" "false"

FINAL_PROOFS="$(count_rows proofs)"
EXPECTED_FINAL_PROOFS="$((INITIAL_PROOFS + 3))"
assert_eq "${EXPECTED_FINAL_PROOFS}" "${FINAL_PROOFS}" "proof row count after smoke test"

log "Smoke test passed"
log "Created references: ${WHOLESALE_REF}, ${RETAIL_REF}, ${NONPROFIT_REF}"
