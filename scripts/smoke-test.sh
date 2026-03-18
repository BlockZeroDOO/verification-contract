#!/usr/bin/env bash

set -euo pipefail

RPC_URL="${RPC_URL:-https://dev-history.globalforce.io}"
MANAGEMENT_ACCOUNT="${MANAGEMENT_ACCOUNT:-managementel}"
VERIFICATION_ACCOUNT="${VERIFICATION_ACCOUNT:-verification}"
PAYMENT_TOKEN_CONTRACT="${PAYMENT_TOKEN_CONTRACT:-eosio.token}"
RETAIL_PRICE="${RETAIL_PRICE:-1.0000 GFT}"
WHOLESALE_PRICE="${WHOLESALE_PRICE:-0.1000 GFT}"
FREE_ENABLED="${FREE_ENABLED:-true}"
FREE_DAILY_LIMIT="${FREE_DAILY_LIMIT:-100}"

: "${OWNER_ACCOUNT:?Set OWNER_ACCOUNT to the management contract admin account.}"
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

SHARED_HASH="${SHARED_HASH:-0123456789abcdef0123456789abcdef0123456789abcdef0123456789abcdef}"
WHOLESALE_HASH="${WHOLESALE_HASH:-${SHARED_HASH}}"
RETAIL_HASH="${RETAIL_HASH:-${SHARED_HASH}}"
NONPROFIT_HASH="${NONPROFIT_HASH:-${SHARED_HASH}}"
TIMESTAMP="$(date -u +%Y%m%d%H%M%S)"
WHOLESALE_REF="wh-${TIMESTAMP}"
RETAIL_REF="rt-${TIMESTAMP}"
RETAIL_BURST_REF="rt-fast-${TIMESTAMP}"
NONPROFIT_REF="np-${TIMESTAMP}"
NONPROFIT_DUPLICATE_REF="np-retry-${TIMESTAMP}"
NONPROFIT_LIMIT_REF="np-limit-${TIMESTAMP}"
NONPROFIT_DISABLED_REF="np-disabled-${TIMESTAMP}"
NONPROFIT_REENABLED_REF="np-reenabled-${TIMESTAMP}"
DUPLICATE_RETAIL_REF="${RETAIL_REF}"
INVALID_NONPROFIT_REF="bad|ref"
INVALID_RETAIL_REF="$(printf 'x%.0s' {1..129})"
WHOLESALE_MEMO="${WHOLESALE_HASH}|SHA-256|none|${WHOLESALE_REF}"
RETAIL_MEMO="${RETAIL_HASH}|SHA-256|none|${RETAIL_REF}"
RETAIL_BURST_MEMO="${RETAIL_HASH}|SHA-256|none|${RETAIL_BURST_REF}"
DUPLICATE_RETAIL_MEMO="${RETAIL_HASH}|SHA-256|none|${DUPLICATE_RETAIL_REF}"
INVALID_RETAIL_MEMO="${RETAIL_HASH}|SHA-256|none|${INVALID_RETAIL_REF}"

cleanup() {
    set +e
    cleos -u "${RPC_URL}" push action "${MANAGEMENT_ACCOUNT}" rmwhuser "[\"${WHOLESALE_ACCOUNT}\"]" -p "${OWNER_ACCOUNT}@active" >/dev/null 2>&1
    cleos -u "${RPC_URL}" push action "${MANAGEMENT_ACCOUNT}" rmnporg "[\"${NONPROFIT_ACCOUNT}\"]" -p "${OWNER_ACCOUNT}@active" >/dev/null 2>&1
    cleos -u "${RPC_URL}" push action "${MANAGEMENT_ACCOUNT}" rmnporg "[\"${WHOLESALE_ACCOUNT}\"]" -p "${OWNER_ACCOUNT}@active" >/dev/null 2>&1
    cleos -u "${RPC_URL}" push action "${MANAGEMENT_ACCOUNT}" rmnporg "[\"${RETAIL_ACCOUNT}\"]" -p "${OWNER_ACCOUNT}@active" >/dev/null 2>&1
}

trap cleanup EXIT

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

assert_contains_account() {
    local account="$1"
    local table_json="$2"
    local exists

    exists="$(printf '%s' "${table_json}" | "${JQ_BIN}" --arg account "${account}" 'any(.rows[]?; .account == $account)')"
    assert_eq "true" "${exists}" "account '${account}' should exist in table"
}

assert_paytoken_config() {
    local table_json
    local found

    table_json="$(get_table_json "${MANAGEMENT_ACCOUNT}" "${MANAGEMENT_ACCOUNT}" paytokens)"
    found="$(printf '%s' "${table_json}" | "${JQ_BIN}" -r \
        --arg token_contract "${PAYMENT_TOKEN_CONTRACT}" \
        --arg retail_price "${RETAIL_PRICE}" \
        --arg wholesale_price "${WHOLESALE_PRICE}" \
        '.rows[]
        | select(.token_contract == $token_contract)
        | select(.retail_price == $retail_price)
        | select(.wholesale_price == $wholesale_price)
        | .token_contract' | tail -n 1)"

    if [[ -z "${found}" ]]; then
        echo "Assertion failed: updated payment token config was not found in paytokens." >&2
        exit 1
    fi
}

get_singleton_field() {
    local code="$1"
    local scope="$2"
    local table="$3"
    local field="$4"
    get_table_json "${code}" "${scope}" "${table}" | "${JQ_BIN}" -r --arg field "${field}" '.rows[0]?[$field] // empty'
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
cleos -u "${RPC_URL}" push action "${MANAGEMENT_ACCOUNT}" setpaytoken "[\"${PAYMENT_TOKEN_CONTRACT}\",\"${RETAIL_PRICE}\",\"${WHOLESALE_PRICE}\"]" -p "${OWNER_ACCOUNT}@active"
assert_paytoken_config

INVALID_RETAIL_PRICE="$(append_precision_zero "${RETAIL_PRICE}")"
INVALID_WHOLESALE_PRICE="$(append_precision_zero "${WHOLESALE_PRICE}")"

log "Verifying setpaytoken rejects precision mismatches against token stat"
if cleos -u "${RPC_URL}" push action "${MANAGEMENT_ACCOUNT}" setpaytoken "[\"${PAYMENT_TOKEN_CONTRACT}\",\"${INVALID_RETAIL_PRICE}\",\"${INVALID_WHOLESALE_PRICE}\"]" -p "${OWNER_ACCOUNT}@active" >/dev/null 2>&1; then
    echo "Assertion failed: setpaytoken accepted a token precision that does not match token stat." >&2
    exit 1
fi
assert_paytoken_config

log "Configuring free submission limits"
cleos -u "${RPC_URL}" push action "${MANAGEMENT_ACCOUNT}" setfreecfg "[${FREE_ENABLED},${FREE_DAILY_LIMIT}]" -p "${OWNER_ACCOUNT}@active"

FREE_LIMIT_CONFIGURED="$(get_singleton_field "${MANAGEMENT_ACCOUNT}" "${MANAGEMENT_ACCOUNT}" freepolicy daily_free_limit)"
assert_eq "${FREE_DAILY_LIMIT}" "${FREE_LIMIT_CONFIGURED}" "freepolicy daily_free_limit"

log "Resetting role state"
cleos -u "${RPC_URL}" push action "${MANAGEMENT_ACCOUNT}" rmwhuser "[\"${WHOLESALE_ACCOUNT}\"]" -p "${OWNER_ACCOUNT}@active" >/dev/null 2>&1 || true
cleos -u "${RPC_URL}" push action "${MANAGEMENT_ACCOUNT}" rmnporg "[\"${NONPROFIT_ACCOUNT}\"]" -p "${OWNER_ACCOUNT}@active" >/dev/null 2>&1 || true

log "Adding wholesale account ${WHOLESALE_ACCOUNT}"
cleos -u "${RPC_URL}" push action "${MANAGEMENT_ACCOUNT}" addwhuser "[\"${WHOLESALE_ACCOUNT}\",\"smoke test account\"]" -p "${OWNER_ACCOUNT}@active"
WHOLESALE_TABLE="$(get_table_json "${MANAGEMENT_ACCOUNT}" "${MANAGEMENT_ACCOUNT}" wholesale)"
assert_contains_account "${WHOLESALE_ACCOUNT}" "${WHOLESALE_TABLE}"

log "Submitting wholesale payment"
cleos -u "${RPC_URL}" push action "${PAYMENT_TOKEN_CONTRACT}" transfer "[\"${WHOLESALE_ACCOUNT}\",\"${MANAGEMENT_ACCOUNT}\",\"${WHOLESALE_PRICE}\",\"${WHOLESALE_MEMO}\"]" -p "${WHOLESALE_ACCOUNT}@active"
assert_proof_by_reference "${WHOLESALE_REF}" "${WHOLESALE_ACCOUNT}" "${MANAGEMENT_ACCOUNT}"

log "Removing wholesale status"
cleos -u "${RPC_URL}" push action "${MANAGEMENT_ACCOUNT}" rmwhuser "[\"${WHOLESALE_ACCOUNT}\"]" -p "${OWNER_ACCOUNT}@active"

log "Submitting retail payment"
cleos -u "${RPC_URL}" push action "${PAYMENT_TOKEN_CONTRACT}" transfer "[\"${RETAIL_ACCOUNT}\",\"${MANAGEMENT_ACCOUNT}\",\"${RETAIL_PRICE}\",\"${RETAIL_MEMO}\"]" -p "${RETAIL_ACCOUNT}@active"
assert_proof_by_reference "${RETAIL_REF}" "${RETAIL_ACCOUNT}" "${MANAGEMENT_ACCOUNT}"

log "Verifying paid submissions are not throttled by nonprofit cooldown"
cleos -u "${RPC_URL}" push action "${PAYMENT_TOKEN_CONTRACT}" transfer "[\"${RETAIL_ACCOUNT}\",\"${MANAGEMENT_ACCOUNT}\",\"${RETAIL_PRICE}\",\"${RETAIL_BURST_MEMO}\"]" -p "${RETAIL_ACCOUNT}@active"
assert_proof_by_reference "${RETAIL_BURST_REF}" "${RETAIL_ACCOUNT}" "${MANAGEMENT_ACCOUNT}"

log "Verifying invalid paid client_reference is rejected"
if cleos -u "${RPC_URL}" push action "${PAYMENT_TOKEN_CONTRACT}" transfer "[\"${RETAIL_ACCOUNT}\",\"${MANAGEMENT_ACCOUNT}\",\"${RETAIL_PRICE}\",\"${INVALID_RETAIL_MEMO}\"]" -p "${RETAIL_ACCOUNT}@active" >/dev/null 2>&1; then
    echo "Assertion failed: invalid paid client_reference was accepted." >&2
    exit 1
fi

log "Verifying duplicate client_reference is rejected for the same submitter"
if cleos -u "${RPC_URL}" push action "${PAYMENT_TOKEN_CONTRACT}" transfer "[\"${RETAIL_ACCOUNT}\",\"${MANAGEMENT_ACCOUNT}\",\"${RETAIL_PRICE}\",\"${DUPLICATE_RETAIL_MEMO}\"]" -p "${RETAIL_ACCOUNT}@active" >/dev/null 2>&1; then
    echo "Assertion failed: duplicate client_reference was accepted for the same submitter." >&2
    exit 1
fi

log "Adding nonprofit account ${NONPROFIT_ACCOUNT}"
cleos -u "${RPC_URL}" push action "${MANAGEMENT_ACCOUNT}" addnporg "[\"${NONPROFIT_ACCOUNT}\",\"smoke test nonprofit\"]" -p "${OWNER_ACCOUNT}@active"

log "Verifying invalid nonprofit client_reference is rejected"
if cleos -u "${RPC_URL}" push action "${MANAGEMENT_ACCOUNT}" submitfree "[\"${NONPROFIT_ACCOUNT}\",\"${NONPROFIT_HASH}\",\"SHA-256\",\"none\",\"${INVALID_NONPROFIT_REF}\"]" -p "${NONPROFIT_ACCOUNT}@active" >/dev/null 2>&1; then
    echo "Assertion failed: invalid nonprofit client_reference was accepted." >&2
    exit 1
fi

log "Submitting nonprofit proof without payment"
cleos -u "${RPC_URL}" push action "${MANAGEMENT_ACCOUNT}" submitfree "[\"${NONPROFIT_ACCOUNT}\",\"${NONPROFIT_HASH}\",\"SHA-256\",\"none\",\"${NONPROFIT_REF}\"]" -p "${NONPROFIT_ACCOUNT}@active"
assert_proof_by_reference "${NONPROFIT_REF}" "${NONPROFIT_ACCOUNT}" "${MANAGEMENT_ACCOUNT}"

FREE_USED_AFTER_NONPROFIT="$(get_singleton_field "${MANAGEMENT_ACCOUNT}" "${MANAGEMENT_ACCOUNT}" freepolicy used_in_window)"
assert_eq "1" "${FREE_USED_AFTER_NONPROFIT}" "freepolicy used_in_window after nonprofit submission"

log "Verifying nonprofit cooldown is enforced"
if cleos -u "${RPC_URL}" push action "${MANAGEMENT_ACCOUNT}" submitfree "[\"${NONPROFIT_ACCOUNT}\",\"${NONPROFIT_HASH}\",\"SHA-256\",\"none\",\"${NONPROFIT_DUPLICATE_REF}\"]" -p "${NONPROFIT_ACCOUNT}@active" >/dev/null 2>&1; then
    echo "Assertion failed: nonprofit cooldown was not enforced." >&2
    exit 1
fi

log "Reducing daily free limit to current usage"
cleos -u "${RPC_URL}" push action "${MANAGEMENT_ACCOUNT}" setfreecfg "[true,1]" -p "${OWNER_ACCOUNT}@active"

log "Adding second nonprofit account for daily limit check"
cleos -u "${RPC_URL}" push action "${MANAGEMENT_ACCOUNT}" addnporg "[\"${WHOLESALE_ACCOUNT}\",\"daily limit probe\"]" -p "${OWNER_ACCOUNT}@active"

log "Verifying daily_free_limit is enforced across nonprofit accounts"
if cleos -u "${RPC_URL}" push action "${MANAGEMENT_ACCOUNT}" submitfree "[\"${WHOLESALE_ACCOUNT}\",\"${NONPROFIT_HASH}\",\"SHA-256\",\"none\",\"${NONPROFIT_LIMIT_REF}\"]" -p "${WHOLESALE_ACCOUNT}@active" >/dev/null 2>&1; then
    echo "Assertion failed: daily_free_limit was not enforced." >&2
    exit 1
fi

FREE_USED_AFTER_LIMIT_REJECT="$(get_singleton_field "${MANAGEMENT_ACCOUNT}" "${MANAGEMENT_ACCOUNT}" freepolicy used_in_window)"
assert_eq "1" "${FREE_USED_AFTER_LIMIT_REJECT}" "freepolicy used_in_window after daily limit rejection"

log "Disabling free submissions"
cleos -u "${RPC_URL}" push action "${MANAGEMENT_ACCOUNT}" setfreecfg "[false,1]" -p "${OWNER_ACCOUNT}@active"

FREE_ENABLED_AFTER_DISABLE="$(get_singleton_field "${MANAGEMENT_ACCOUNT}" "${MANAGEMENT_ACCOUNT}" freepolicy enabled)"
FREE_USED_AFTER_DISABLE="$(get_singleton_field "${MANAGEMENT_ACCOUNT}" "${MANAGEMENT_ACCOUNT}" freepolicy used_in_window)"
assert_eq "false" "${FREE_ENABLED_AFTER_DISABLE}" "freepolicy enabled after disable"
assert_eq "1" "${FREE_USED_AFTER_DISABLE}" "freepolicy used_in_window after disable"

log "Verifying disabled free submissions are rejected"
if cleos -u "${RPC_URL}" push action "${MANAGEMENT_ACCOUNT}" submitfree "[\"${WHOLESALE_ACCOUNT}\",\"${NONPROFIT_HASH}\",\"SHA-256\",\"none\",\"${NONPROFIT_DISABLED_REF}\"]" -p "${WHOLESALE_ACCOUNT}@active" >/dev/null 2>&1; then
    echo "Assertion failed: disabled free submissions were accepted." >&2
    exit 1
fi

log "Re-enabling free submissions with the same daily limit"
cleos -u "${RPC_URL}" push action "${MANAGEMENT_ACCOUNT}" setfreecfg "[true,1]" -p "${OWNER_ACCOUNT}@active"

FREE_ENABLED_AFTER_REENABLE="$(get_singleton_field "${MANAGEMENT_ACCOUNT}" "${MANAGEMENT_ACCOUNT}" freepolicy enabled)"
FREE_USED_AFTER_REENABLE="$(get_singleton_field "${MANAGEMENT_ACCOUNT}" "${MANAGEMENT_ACCOUNT}" freepolicy used_in_window)"
assert_eq "true" "${FREE_ENABLED_AFTER_REENABLE}" "freepolicy enabled after re-enable"
assert_eq "1" "${FREE_USED_AFTER_REENABLE}" "freepolicy used_in_window after re-enable"

log "Verifying re-enable does not reset same-day usage"
if cleos -u "${RPC_URL}" push action "${MANAGEMENT_ACCOUNT}" submitfree "[\"${WHOLESALE_ACCOUNT}\",\"${NONPROFIT_HASH}\",\"SHA-256\",\"none\",\"${NONPROFIT_REENABLED_REF}\"]" -p "${WHOLESALE_ACCOUNT}@active" >/dev/null 2>&1; then
    echo "Assertion failed: re-enabling free submissions reset same-day usage." >&2
    exit 1
fi

FINAL_PROOFS="$(count_rows "${VERIFICATION_ACCOUNT}" "${VERIFICATION_ACCOUNT}" proofs)"
EXPECTED_FINAL_PROOFS="$((INITIAL_PROOFS + 4))"
assert_eq "${EXPECTED_FINAL_PROOFS}" "${FINAL_PROOFS}" "proof row count after smoke test"

log "Smoke test passed"
log "Created references: ${WHOLESALE_REF}, ${RETAIL_REF}, ${NONPROFIT_REF}"
