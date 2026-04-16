#!/usr/bin/env bash

set -euo pipefail

RPC_URL="${RPC_URL:-https://jungle4.api.eosnation.io}"
READ_RPC_URL="${READ_RPC_URL:-${RPC_URL}}"
RETPAY_ACCOUNT="${RETPAY_ACCOUNT:-verifretpay}"
VERIFICATION_ACCOUNT="${VERIFICATION_ACCOUNT:-verif}"
OWNER_ACCOUNT="${OWNER_ACCOUNT:-}"
VERIFICATION_OWNER_ACCOUNT="${VERIFICATION_OWNER_ACCOUNT:-${VERIFICATION_ACCOUNT}}"
VERIFICATION_BILLING_ACCOUNT="${VERIFICATION_BILLING_ACCOUNT:-${RETPAY_ACCOUNT}}"
SUBMITTER_ACCOUNT="${SUBMITTER_ACCOUNT:-}"
PAYMENT_TOKEN_CONTRACT="${PAYMENT_TOKEN_CONTRACT:-eosio.token}"
PAYMENT_SYMBOL="${PAYMENT_SYMBOL:-EOS}"
PAYMENT_PRECISION="${PAYMENT_PRECISION:-4}"
PRICE_PER_KIB_SINGLE="${PRICE_PER_KIB_SINGLE:-0.0050 EOS}"
PRICE_PER_KIB_BATCH="${PRICE_PER_KIB_BATCH:-0.0050 EOS}"
BILLABLE_BYTES_SINGLE="${BILLABLE_BYTES_SINGLE:-1536}"
BILLABLE_BYTES_BATCH="${BILLABLE_BYTES_BATCH:-4096}"
WRONG_TOKEN_CONTRACT="${WRONG_TOKEN_CONTRACT:-retail.fake}"
WAIT_TIMEOUT_SEC="${WAIT_TIMEOUT_SEC:-90}"
WAIT_INTERVAL_SEC="${WAIT_INTERVAL_SEC:-1}"

: "${OWNER_ACCOUNT:?Set OWNER_ACCOUNT to the retail payment contract authority account.}"
: "${VERIFICATION_OWNER_ACCOUNT:?Set VERIFICATION_OWNER_ACCOUNT to the verif authority account.}"
: "${SUBMITTER_ACCOUNT:?Set SUBMITTER_ACCOUNT to a funded retail payer/submitter account.}"

if [[ ${#RETPAY_ACCOUNT} -gt 12 ]]; then
    echo "RETPAY_ACCOUNT must be 12 characters or fewer for Antelope account names: ${RETPAY_ACCOUNT}" >&2
    exit 1
fi

if ! command -v cleos >/dev/null 2>&1; then
    echo "cleos is required for smoke-test-retpay.sh" >&2
    exit 1
fi

if command -v jq >/dev/null 2>&1; then
    JQ_BIN="jq"
else
    echo "jq is required for smoke-test-retpay.sh" >&2
    exit 1
fi

hash_text() {
    local input="$1"
    if command -v sha256sum >/dev/null 2>&1; then
        printf '%s' "${input}" | sha256sum | awk '{print $1}'
    elif command -v shasum >/dev/null 2>&1; then
        printf '%s' "${input}" | shasum -a 256 | awk '{print $1}'
    elif command -v openssl >/dev/null 2>&1; then
        printf '%s' "${input}" | openssl dgst -sha256 -binary | xxd -p -c 256
    else
        echo "A SHA-256 tool is required (sha256sum, shasum, or openssl)." >&2
        exit 1
    fi
}

log() {
    printf '[smoke-test-retpay] %s\n' "$1"
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

asset_to_units() {
    local asset="$1"
    local amount="${asset% *}"
    local whole="${amount%%.*}"
    local fraction="${amount#*.}"
    if [[ "${fraction}" == "${amount}" ]]; then
        fraction=""
    fi

    while [[ ${#fraction} -lt ${PAYMENT_PRECISION} ]]; do
        fraction="${fraction}0"
    done
    fraction="${fraction:0:${PAYMENT_PRECISION}}"
    printf '%s\n' "$((10#${whole} * 10**${PAYMENT_PRECISION} + 10#${fraction}))"
}

units_to_asset() {
    local units="$1"
    local symbol="$2"
    local scale=$((10**PAYMENT_PRECISION))
    local whole=$((units / scale))
    local fraction=$((units % scale))
    printf "%d.%0${PAYMENT_PRECISION}d %s\n" "${whole}" "${fraction}" "${symbol}"
}

get_table_json() {
    local code="$1"
    local scope="$2"
    local table="$3"
    cleos -u "${READ_RPC_URL}" get table "${code}" "${scope}" "${table}" --limit 1000
}

wait_for_table_match() {
    local code="$1"
    local scope="$2"
    local table="$3"
    local jq_filter="$4"
    local description="$5"

    local deadline=$(( $(date -u +%s) + WAIT_TIMEOUT_SEC ))
    while true; do
        if get_table_json "${code}" "${scope}" "${table}" | "${JQ_BIN}" -e "${jq_filter}" >/dev/null 2>&1; then
            return 0
        fi

        if (( $(date -u +%s) >= deadline )); then
            echo "Timed out waiting for ${description}." >&2
            exit 1
        fi

        sleep "${WAIT_INTERVAL_SEC}"
    done
}

TIMESTAMP="$(date -u +%Y%m%d%H%M%S)"
BASE_ID="$(date -u +%s)"
SINGLE_KIB="$(( (BILLABLE_BYTES_SINGLE + 1023) / 1024 ))"
BATCH_KIB="$(( (BILLABLE_BYTES_BATCH + 1023) / 1024 ))"
PRICE_SINGLE="$(units_to_asset "$(( SINGLE_KIB * $(asset_to_units "${PRICE_PER_KIB_SINGLE}") ))" "${PAYMENT_SYMBOL}")"
PRICE_BATCH="$(units_to_asset "$(( BATCH_KIB * $(asset_to_units "${PRICE_PER_KIB_BATCH}") ))" "${PAYMENT_SYMBOL}")"
UNDERPAY_SINGLE="$(units_to_asset "$(( SINGLE_KIB * $(asset_to_units "${PRICE_PER_KIB_SINGLE}") - 1 ))" "${PAYMENT_SYMBOL}")"

SCHEMA_ID="${SCHEMA_ID:-$((BASE_ID + 5000))}"
POLICY_SINGLE_ID="${POLICY_SINGLE_ID:-$((BASE_ID + 6000))}"
POLICY_BATCH_ID="${POLICY_BATCH_ID:-$((BASE_ID + 6001))}"

SINGLE_EXTREF="$(hash_text "retpay-single-${TIMESTAMP}")"
SINGLE_OBJECT_HASH="$(hash_text "retpay-object-${TIMESTAMP}")"
SINGLE_EXTREF_DUPLICATE="$(hash_text "retpay-duplicate-${TIMESTAMP}")"
BATCH_EXTREF="$(hash_text "retpay-batch-${TIMESTAMP}")"
BATCH_ROOT_HASH="$(hash_text "retpay-root-${TIMESTAMP}")"
MANIFEST_HASH="$(hash_text "retpay-manifest-${TIMESTAMP}")"

log "Configuring verification authorization sources"
cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" setauthsrcs \
    "[\"${VERIFICATION_BILLING_ACCOUNT}\",\"${RETPAY_ACCOUNT}\"]" \
    -p "${VERIFICATION_OWNER_ACCOUNT}@active"

log "Creating retail schema"
cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" addschema \
    "[${SCHEMA_ID},\"1.0.0\",\"$(hash_text "retpay-schema-${TIMESTAMP}")\",\"$(hash_text "retpay-schema-policy-${TIMESTAMP}")\"]" \
    -p "${VERIFICATION_OWNER_ACCOUNT}@active"

log "Creating retail single policy"
cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" setpolicy \
    "[${POLICY_SINGLE_ID},true,false,true]" \
    -p "${VERIFICATION_OWNER_ACCOUNT}@active"

log "Creating retail batch policy"
cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" setpolicy \
    "[${POLICY_BATCH_ID},false,true,true]" \
    -p "${VERIFICATION_OWNER_ACCOUNT}@active"

log "Configuring accepted retail payment token"
cleos -u "${RPC_URL}" push action "${RETPAY_ACCOUNT}" settoken \
    "[\"${PAYMENT_TOKEN_CONTRACT}\",\"${PAYMENT_PRECISION},${PAYMENT_SYMBOL}\"]" \
    -p "${OWNER_ACCOUNT}@active"

log "Configuring verification account for retail orchestration"
cleos -u "${RPC_URL}" push action "${RETPAY_ACCOUNT}" setverifacct \
    "[\"${VERIFICATION_ACCOUNT}\"]" \
    -p "${OWNER_ACCOUNT}@active"

log "Configuring retail single tariff"
cleos -u "${RPC_URL}" push action "${RETPAY_ACCOUNT}" setprice \
    "[0,\"${PAYMENT_TOKEN_CONTRACT}\",\"${PRICE_PER_KIB_SINGLE}\"]" \
    -p "${OWNER_ACCOUNT}@active"

log "Configuring retail batch tariff"
cleos -u "${RPC_URL}" push action "${RETPAY_ACCOUNT}" setprice \
    "[1,\"${PAYMENT_TOKEN_CONTRACT}\",\"${PRICE_PER_KIB_BATCH}\"]" \
    -p "${OWNER_ACCOUNT}@active"

log "Rejecting underpayment for atomic retail single flow"
if cleos -u "${RPC_URL}" transfer "${SUBMITTER_ACCOUNT}" "${RETPAY_ACCOUNT}" "${UNDERPAY_SINGLE}" \
    "single|${SUBMITTER_ACCOUNT}|${SCHEMA_ID}|${POLICY_SINGLE_ID}|${SINGLE_OBJECT_HASH}|${SINGLE_EXTREF}|${BILLABLE_BYTES_SINGLE}" >/dev/null 2>&1; then
    echo "Assertion failed: underpayment retail transfer was accepted." >&2
    exit 1
fi

log "Rejecting wrong token for atomic retail single flow"
if cleos -u "${RPC_URL}" push action "${WRONG_TOKEN_CONTRACT}" transfer \
    "[\"${SUBMITTER_ACCOUNT}\",\"${RETPAY_ACCOUNT}\",\"${PRICE_SINGLE}\",\"single|${SUBMITTER_ACCOUNT}|${SCHEMA_ID}|${POLICY_SINGLE_ID}|${SINGLE_OBJECT_HASH}|${SINGLE_EXTREF}|${BILLABLE_BYTES_SINGLE}\"]" \
    -p "${SUBMITTER_ACCOUNT}@active" >/dev/null 2>&1; then
    echo "Assertion failed: wrong-token retail transfer was accepted." >&2
    exit 1
fi

log "Funding atomic retail single transfer"
cleos -u "${RPC_URL}" transfer "${SUBMITTER_ACCOUNT}" "${RETPAY_ACCOUNT}" "${PRICE_SINGLE}" \
    "single|${SUBMITTER_ACCOUNT}|${SCHEMA_ID}|${POLICY_SINGLE_ID}|${SINGLE_OBJECT_HASH}|${SINGLE_EXTREF}|${BILLABLE_BYTES_SINGLE}"

wait_for_table_match \
    "${VERIFICATION_ACCOUNT}" \
    "${VERIFICATION_ACCOUNT}" \
    "commitments" \
    ".rows[] | select(.external_ref == \"${SINGLE_EXTREF}\")" \
    "retail commitment ${SINGLE_EXTREF}"

COMMITMENT_ID="$(get_table_json "${VERIFICATION_ACCOUNT}" "${VERIFICATION_ACCOUNT}" commitments | "${JQ_BIN}" -r \
    --arg external_ref "${SINGLE_EXTREF}" \
    '.rows[] | select(.external_ref == $external_ref) | .id' | tail -n 1)"
COMMITMENT_BYTES="$(get_table_json "${VERIFICATION_ACCOUNT}" "${VERIFICATION_ACCOUNT}" commitments | "${JQ_BIN}" -r \
    --argjson id "${COMMITMENT_ID}" \
    '.rows[] | select(.id == $id) | .billable_bytes')"
COMMITMENT_KIB="$(get_table_json "${VERIFICATION_ACCOUNT}" "${VERIFICATION_ACCOUNT}" commitments | "${JQ_BIN}" -r \
    --argjson id "${COMMITMENT_ID}" \
    '.rows[] | select(.id == $id) | .billable_kib')"
assert_eq "${BILLABLE_BYTES_SINGLE}" "${COMMITMENT_BYTES}" "retail commitment billable bytes"
assert_eq "${SINGLE_KIB}" "${COMMITMENT_KIB}" "retail commitment billable kib"

log "Rejecting atomic retail single transfer with invalid policy"
if cleos -u "${RPC_URL}" transfer "${SUBMITTER_ACCOUNT}" "${RETPAY_ACCOUNT}" "${PRICE_SINGLE}" \
    "single|${SUBMITTER_ACCOUNT}|${SCHEMA_ID}|${POLICY_BATCH_ID}|$(hash_text "retpay-invalid-policy-object-${TIMESTAMP}")|$(hash_text "retpay-invalid-policy-ext-${TIMESTAMP}")|${BILLABLE_BYTES_SINGLE}" >/dev/null 2>&1; then
    echo "Assertion failed: atomic retail single transfer with invalid policy was accepted." >&2
    exit 1
fi

log "Rejecting duplicate atomic retail single request"
if cleos -u "${RPC_URL}" transfer "${SUBMITTER_ACCOUNT}" "${RETPAY_ACCOUNT}" "${PRICE_SINGLE}" \
    "single|${SUBMITTER_ACCOUNT}|${SCHEMA_ID}|${POLICY_SINGLE_ID}|$(hash_text "retpay-duplicate-object-${TIMESTAMP}")|${SINGLE_EXTREF}|${BILLABLE_BYTES_SINGLE}" >/dev/null 2>&1; then
    echo "Assertion failed: duplicate atomic retail single request was accepted." >&2
    exit 1
fi

log "Funding second atomic retail single transfer with fresh request"
cleos -u "${RPC_URL}" transfer "${SUBMITTER_ACCOUNT}" "${RETPAY_ACCOUNT}" "${PRICE_SINGLE}" \
    "single|${SUBMITTER_ACCOUNT}|${SCHEMA_ID}|${POLICY_SINGLE_ID}|$(hash_text "retpay-second-object-${TIMESTAMP}")|${SINGLE_EXTREF_DUPLICATE}|${BILLABLE_BYTES_SINGLE}"

log "Funding atomic retail batch transfer"
cleos -u "${RPC_URL}" transfer "${SUBMITTER_ACCOUNT}" "${RETPAY_ACCOUNT}" "${PRICE_BATCH}" \
    "batch|${SUBMITTER_ACCOUNT}|${SCHEMA_ID}|${POLICY_BATCH_ID}|${BATCH_ROOT_HASH}|2|${MANIFEST_HASH}|${BATCH_EXTREF}|${BILLABLE_BYTES_BATCH}"

wait_for_table_match \
    "${VERIFICATION_ACCOUNT}" \
    "${VERIFICATION_ACCOUNT}" \
    "batches" \
    ".rows[] | select(.external_ref == \"${BATCH_EXTREF}\")" \
    "retail batch ${BATCH_EXTREF}"

BATCH_ID="$(get_table_json "${VERIFICATION_ACCOUNT}" "${VERIFICATION_ACCOUNT}" batches | "${JQ_BIN}" -r \
    --arg external_ref "${BATCH_EXTREF}" \
    '.rows[] | select(.external_ref == $external_ref) | .id' | tail -n 1)"
BATCH_BYTES="$(get_table_json "${VERIFICATION_ACCOUNT}" "${VERIFICATION_ACCOUNT}" batches | "${JQ_BIN}" -r \
    --argjson id "${BATCH_ID}" \
    '.rows[] | select(.id == $id) | .billable_bytes')"
BATCH_BILLABLE_KIB="$(get_table_json "${VERIFICATION_ACCOUNT}" "${VERIFICATION_ACCOUNT}" batches | "${JQ_BIN}" -r \
    --argjson id "${BATCH_ID}" \
    '.rows[] | select(.id == $id) | .billable_kib')"
assert_eq "${BILLABLE_BYTES_BATCH}" "${BATCH_BYTES}" "retail batch billable bytes"
assert_eq "${BATCH_KIB}" "${BATCH_BILLABLE_KIB}" "retail batch billable kib"

log "Retail payment smoke test passed"
