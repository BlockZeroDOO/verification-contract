#!/usr/bin/env bash

set -euo pipefail

RPC_URL="${RPC_URL:-https://history.denotary.io}"
VERIFICATION_ACCOUNT="${VERIFICATION_ACCOUNT:-verification}"
PAYMENT_TOKEN_CONTRACT="${PAYMENT_TOKEN_CONTRACT:-eosio.token}"
PAYMENT_PRICE="${PAYMENT_PRICE:-1.0000 GFT}"

: "${OWNER_ACCOUNT:?Set OWNER_ACCOUNT to the verification contract account.}"
: "${PAYER_ACCOUNT:?Set PAYER_ACCOUNT to a funded test account.}"

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

SHARED_HASH="${SHARED_HASH:-0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef}"
TIMESTAMP="$(date -u +%Y%m%d%H%M%S)"
PAYMENT_REF="pay-${TIMESTAMP}"
DUPLICATE_PAYMENT_REF="${PAYMENT_REF}"
INVALID_PAYMENT_REF="$(printf 'x%.0s' {1..129})"
PAYMENT_MEMO="${SHARED_HASH}|SHA-256|none|${PAYMENT_REF}"
DUPLICATE_PAYMENT_MEMO="${SHARED_HASH}|SHA-256|none|${DUPLICATE_PAYMENT_REF}"
INVALID_PAYMENT_MEMO="${SHARED_HASH}|SHA-256|none|${INVALID_PAYMENT_REF}"

log() {
    printf '[smoke-test] %s\n' "$1"
}

append_precision_zero() {
    local asset_string="$1"
    local amount="${asset_string% *}"
    local symbol="${asset_string#* }"

    if [[ "${amount}" == *.* ]]; then
        printf '%s0 %s\n' "${amount}" "${symbol}"
    else
        printf '%s.0 %s\n' "${amount}" "${symbol}"
    fi
}

smallest_positive_amount() {
    local asset_string="$1"
    local amount="${asset_string% *}"
    local symbol="${asset_string#* }"

    if [[ "${amount}" == *.* ]]; then
        local decimals="${amount#*.}"
        local precision="${#decimals}"
        local zeros_count=$((precision - 1))
        local zeros=""

        if (( zeros_count > 0 )); then
            zeros="$(printf '%0.s0' $(seq 1 "${zeros_count}"))"
        fi

        printf '0.%s1 %s\n' "${zeros}" "${symbol}"
    else
        printf '1 %s\n' "${symbol}"
    fi
}

get_table_json() {
    local code="$1"
    local scope="$2"
    local table="$3"
    cleos -u "${RPC_URL}" get table "${code}" "${scope}" "${table}"
}

count_rows() {
    local code="$1"
    local scope="$2"
    local table="$3"
    get_table_json "${code}" "${scope}" "${table}" | "${JQ_BIN}" '.rows | length'
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

assert_paytoken_config() {
    local table_json
    local found

    table_json="$(get_table_json "${VERIFICATION_ACCOUNT}" "${VERIFICATION_ACCOUNT}" paytokens)"
    found="$(printf '%s' "${table_json}" | "${JQ_BIN}" -r \
        --arg token_contract "${PAYMENT_TOKEN_CONTRACT}" \
        --arg price "${PAYMENT_PRICE}" \
        '.rows[]
        | select(.token_contract == $token_contract)
        | select(.price == $price)
        | .token_contract' | tail -n 1)"

    if [[ -z "${found}" ]]; then
        echo "Assertion failed: updated payment token config was not found in paytokens." >&2
        exit 1
    fi
}

assert_proof_by_reference() {
    local reference="$1"
    local expected_submitter="$2"
    local expected_writer="$3"

    local proofs_json proof_json submitter writer
    proofs_json="$(get_table_json "${VERIFICATION_ACCOUNT}" "${VERIFICATION_ACCOUNT}" proofs)"
    proof_json="$(printf '%s' "${proofs_json}" | "${JQ_BIN}" -c --arg ref "${reference}" '.rows[] | select(.client_reference == $ref)' | tail -n 1)"

    if [[ -z "${proof_json}" ]]; then
        echo "Assertion failed: proof with client_reference '${reference}' was not found." >&2
        exit 1
    fi

    submitter="$(printf '%s' "${proof_json}" | "${JQ_BIN}" -r '.submitter')"
    writer="$(printf '%s' "${proof_json}" | "${JQ_BIN}" -r '.writer')"

    assert_eq "${expected_submitter}" "${submitter}" "submitter for reference '${reference}'"
    assert_eq "${expected_writer}" "${writer}" "writer for reference '${reference}'"
}

log "Initial proof count"
INITIAL_PROOFS="$(count_rows "${VERIFICATION_ACCOUNT}" "${VERIFICATION_ACCOUNT}" proofs)"

log "Ensuring payment token config exists"
cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" setpaytoken "[\"${PAYMENT_TOKEN_CONTRACT}\",\"${PAYMENT_PRICE}\"]" -p "${OWNER_ACCOUNT}@active"
assert_paytoken_config

INVALID_PAYMENT_PRICE="$(append_precision_zero "${PAYMENT_PRICE}")"

log "Verifying setpaytoken rejects precision mismatches against token stat"
if cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" setpaytoken "[\"${PAYMENT_TOKEN_CONTRACT}\",\"${INVALID_PAYMENT_PRICE}\"]" -p "${OWNER_ACCOUNT}@active" >/dev/null 2>&1; then
    echo "Assertion failed: setpaytoken accepted a token precision that does not match token stat." >&2
    exit 1
fi
assert_paytoken_config

log "Submitting paid proof directly to verification"
cleos -u "${RPC_URL}" push action "${PAYMENT_TOKEN_CONTRACT}" transfer "[\"${PAYER_ACCOUNT}\",\"${VERIFICATION_ACCOUNT}\",\"${PAYMENT_PRICE}\",\"${PAYMENT_MEMO}\"]" -p "${PAYER_ACCOUNT}@active"
assert_proof_by_reference "${PAYMENT_REF}" "${PAYER_ACCOUNT}" "${VERIFICATION_ACCOUNT}"

log "Verifying invalid paid client_reference is rejected"
if cleos -u "${RPC_URL}" push action "${PAYMENT_TOKEN_CONTRACT}" transfer "[\"${PAYER_ACCOUNT}\",\"${VERIFICATION_ACCOUNT}\",\"${PAYMENT_PRICE}\",\"${INVALID_PAYMENT_MEMO}\"]" -p "${PAYER_ACCOUNT}@active" >/dev/null 2>&1; then
    echo "Assertion failed: invalid paid client_reference was accepted." >&2
    exit 1
fi

log "Verifying duplicate client_reference is rejected for the same submitter"
if cleos -u "${RPC_URL}" push action "${PAYMENT_TOKEN_CONTRACT}" transfer "[\"${PAYER_ACCOUNT}\",\"${VERIFICATION_ACCOUNT}\",\"${PAYMENT_PRICE}\",\"${DUPLICATE_PAYMENT_MEMO}\"]" -p "${PAYER_ACCOUNT}@active" >/dev/null 2>&1; then
    echo "Assertion failed: duplicate client_reference was accepted for the same submitter." >&2
    exit 1
fi

log "Verifying incorrect payment amount is rejected"
WRONG_PAYMENT_AMOUNT="$(smallest_positive_amount "${PAYMENT_PRICE}")"
if cleos -u "${RPC_URL}" push action "${PAYMENT_TOKEN_CONTRACT}" transfer "[\"${PAYER_ACCOUNT}\",\"${VERIFICATION_ACCOUNT}\",\"${WRONG_PAYMENT_AMOUNT}\",\"${SHARED_HASH}|SHA-256|none|wrong-amount-${TIMESTAMP}\"]" -p "${PAYER_ACCOUNT}@active" >/dev/null 2>&1; then
    echo "Assertion failed: incorrect payment amount was accepted." >&2
    exit 1
fi

FINAL_PROOFS="$(count_rows "${VERIFICATION_ACCOUNT}" "${VERIFICATION_ACCOUNT}" proofs)"
EXPECTED_FINAL_PROOFS="$((INITIAL_PROOFS + 1))"
assert_eq "${EXPECTED_FINAL_PROOFS}" "${FINAL_PROOFS}" "proof row count after smoke test"

log "Smoke test passed"
log "Created reference: ${PAYMENT_REF}"
