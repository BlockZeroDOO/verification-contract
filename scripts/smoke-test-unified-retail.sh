#!/usr/bin/env bash

set -euo pipefail

RPC_URL="${RPC_URL:-https://jungle4.api.eosnation.io}"
READ_RPC_URL="${READ_RPC_URL:-${RPC_URL}}"
VERIFICATION_ACCOUNT="${VERIFICATION_ACCOUNT:-verif}"
VERIFICATION_BILLING_ACCOUNT="${VERIFICATION_BILLING_ACCOUNT:-verifbill}"
RETPAY_ACCOUNT="${RETPAY_ACCOUNT:-verifretpay}"
OWNER_ACCOUNT="${OWNER_ACCOUNT:-}"
RETPAY_OWNER_ACCOUNT="${RETPAY_OWNER_ACCOUNT:-${RETPAY_ACCOUNT}}"
SUBMITTER_ACCOUNT="${SUBMITTER_ACCOUNT:-}"
PAYMENT_TOKEN_CONTRACT="${PAYMENT_TOKEN_CONTRACT:-eosio.token}"
PAYMENT_SYMBOL="${PAYMENT_SYMBOL:-EOS}"
PAYMENT_PRECISION="${PAYMENT_PRECISION:-4}"
PRICE_PER_KIB_SINGLE="${PRICE_PER_KIB_SINGLE:-0.0050 EOS}"
PRICE_PER_KIB_BATCH="${PRICE_PER_KIB_BATCH:-0.0050 EOS}"
WAIT_TIMEOUT_SEC="${WAIT_TIMEOUT_SEC:-90}"
WAIT_INTERVAL_SEC="${WAIT_INTERVAL_SEC:-1}"

: "${OWNER_ACCOUNT:?Set OWNER_ACCOUNT to the verification contract authority account.}"
: "${SUBMITTER_ACCOUNT:?Set SUBMITTER_ACCOUNT to a funded account that can sign submits.}"
: "${RETPAY_OWNER_ACCOUNT:?Set RETPAY_OWNER_ACCOUNT to the retail payment contract authority account.}"

if ! command -v cleos >/dev/null 2>&1; then
    echo "cleos is required for smoke-test-unified-retail.sh" >&2
    exit 1
fi

if command -v jq >/dev/null 2>&1; then
    JQ_BIN="jq"
else
    echo "jq is required for smoke-test-unified-retail.sh" >&2
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
    printf '[smoke-test-unified-retail] %s\n' "$1"
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

assert_eq() {
    local expected="$1"
    local actual="$2"
    local message="$3"

    if [[ "${expected}" != "${actual}" ]]; then
        echo "Assertion failed: ${message}. Expected '${expected}', got '${actual}'." >&2
        exit 1
    fi
}

get_commitment_id_by_external_ref() {
    local external_ref="$1"
    wait_for_table_match \
        "${VERIFICATION_ACCOUNT}" \
        "${VERIFICATION_ACCOUNT}" \
        "commitments" \
        ".rows[] | select(.external_ref == \"${external_ref}\")" \
        "commitment with external_ref ${external_ref}"

    get_table_json "${VERIFICATION_ACCOUNT}" "${VERIFICATION_ACCOUNT}" commitments | "${JQ_BIN}" -r \
        --arg external_ref "${external_ref}" \
        '.rows[] | select(.external_ref == $external_ref) | .id' | tail -n 1
}

get_batch_id_by_external_ref() {
    local external_ref="$1"
    wait_for_table_match \
        "${VERIFICATION_ACCOUNT}" \
        "${VERIFICATION_ACCOUNT}" \
        "batches" \
        ".rows[] | select(.external_ref == \"${external_ref}\")" \
        "batch with external_ref ${external_ref}"

    get_table_json "${VERIFICATION_ACCOUNT}" "${VERIFICATION_ACCOUNT}" batches | "${JQ_BIN}" -r \
        --arg external_ref "${external_ref}" \
        '.rows[] | select(.external_ref == $external_ref) | .id' | tail -n 1
}

TIMESTAMP="$(date -u +%Y%m%d%H%M%S)"
BASE_ID="$(date -u +%s)"
EXPECTED_SINGLE_BYTES=88
EXPECTED_BATCH_BYTES=124
SINGLE_KIB="$(( (EXPECTED_SINGLE_BYTES + 1023) / 1024 ))"
BATCH_KIB="$(( (EXPECTED_BATCH_BYTES + 1023) / 1024 ))"
PRICE_SINGLE="$(units_to_asset "$(( SINGLE_KIB * $(asset_to_units "${PRICE_PER_KIB_SINGLE}") ))" "${PAYMENT_SYMBOL}")"
PRICE_BATCH="$(units_to_asset "$(( BATCH_KIB * $(asset_to_units "${PRICE_PER_KIB_BATCH}") ))" "${PAYMENT_SYMBOL}")"

SCHEMA_ID="${SCHEMA_ID:-$((BASE_ID + 5000))}"
POLICY_SINGLE_ID="${POLICY_SINGLE_ID:-$((BASE_ID + 6000))}"
POLICY_BATCH_ID="${POLICY_BATCH_ID:-$((BASE_ID + 6001))}"

SINGLE_EXTREF="$(hash_text "unified-retail-single-${TIMESTAMP}")"
SINGLE_EXTREF_MISMATCH="$(hash_text "unified-retail-mismatch-${TIMESTAMP}")"
SINGLE_OBJECT_HASH="$(hash_text "unified-retail-object-${TIMESTAMP}")"
BATCH_EXTREF="$(hash_text "unified-retail-batch-${TIMESTAMP}")"
BATCH_ROOT_HASH="$(hash_text "unified-retail-root-${TIMESTAMP}")"
MANIFEST_HASH="$(hash_text "unified-retail-manifest-${TIMESTAMP}")"

log "Configuring verification authorization sources"
cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" setauthsrcs \
    "[\"${VERIFICATION_BILLING_ACCOUNT}\",\"${RETPAY_ACCOUNT}\"]" \
    -p "${OWNER_ACCOUNT}@active"

log "Configuring retail payment token"
cleos -u "${RPC_URL}" push action "${RETPAY_ACCOUNT}" settoken \
    "[\"${PAYMENT_TOKEN_CONTRACT}\",\"${PAYMENT_PRECISION},${PAYMENT_SYMBOL}\"]" \
    -p "${RETPAY_OWNER_ACCOUNT}@active"

log "Configuring verification account for retail consume authorization"
cleos -u "${RPC_URL}" push action "${RETPAY_ACCOUNT}" setverifacct \
    "[\"${VERIFICATION_ACCOUNT}\"]" \
    -p "${RETPAY_OWNER_ACCOUNT}@active"

log "Configuring retail single tariff"
cleos -u "${RPC_URL}" push action "${RETPAY_ACCOUNT}" setprice \
    "[0,\"${PAYMENT_TOKEN_CONTRACT}\",\"${PRICE_PER_KIB_SINGLE}\"]" \
    -p "${RETPAY_OWNER_ACCOUNT}@active"

log "Configuring retail batch tariff"
cleos -u "${RPC_URL}" push action "${RETPAY_ACCOUNT}" setprice \
    "[1,\"${PAYMENT_TOKEN_CONTRACT}\",\"${PRICE_PER_KIB_BATCH}\"]" \
    -p "${RETPAY_OWNER_ACCOUNT}@active"

log "Creating unified retail schema"
cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" addschema \
    "[${SCHEMA_ID},\"1.0.0\",\"$(hash_text "unified-retail-schema-${TIMESTAMP}")\",\"$(hash_text "unified-retail-policy-${TIMESTAMP}")\"]" \
    -p "${OWNER_ACCOUNT}@active"

log "Creating unified retail single policy"
cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" setpolicy \
    "[${POLICY_SINGLE_ID},true,false,true]" \
    -p "${OWNER_ACCOUNT}@active"

log "Creating unified retail batch policy"
cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" setpolicy \
    "[${POLICY_BATCH_ID},false,true,true]" \
    -p "${OWNER_ACCOUNT}@active"

log "Funding unified retail single authorization"
cleos -u "${RPC_URL}" transfer \
    "${SUBMITTER_ACCOUNT}" \
    "${RETPAY_ACCOUNT}" \
    "${PRICE_SINGLE}" \
    "single|${SUBMITTER_ACCOUNT}|${SCHEMA_ID}|${POLICY_SINGLE_ID}|${SINGLE_OBJECT_HASH}|${SINGLE_EXTREF}"

COMMITMENT_ID="$(get_commitment_id_by_external_ref "${SINGLE_EXTREF}")"
COMMITMENT_SUBMITTER="$(get_table_json "${VERIFICATION_ACCOUNT}" "${VERIFICATION_ACCOUNT}" commitments | "${JQ_BIN}" -r \
    --argjson id "${COMMITMENT_ID}" '.rows[] | select(.id == $id) | .submitter')"
COMMITMENT_BYTES="$(get_table_json "${VERIFICATION_ACCOUNT}" "${VERIFICATION_ACCOUNT}" commitments | "${JQ_BIN}" -r \
    --argjson id "${COMMITMENT_ID}" '.rows[] | select(.id == $id) | .billable_bytes')"
COMMITMENT_KIB="$(get_table_json "${VERIFICATION_ACCOUNT}" "${VERIFICATION_ACCOUNT}" commitments | "${JQ_BIN}" -r \
    --argjson id "${COMMITMENT_ID}" '.rows[] | select(.id == $id) | .billable_kib')"
assert_eq "${SUBMITTER_ACCOUNT}" "${COMMITMENT_SUBMITTER}" "unified retail commitment submitter"
assert_eq "${EXPECTED_SINGLE_BYTES}" "${COMMITMENT_BYTES}" "unified retail commitment billable bytes"
assert_eq "${SINGLE_KIB}" "${COMMITMENT_KIB}" "unified retail commitment billable kib"

log "Rejecting atomic retail single transfer with invalid policy"
if cleos -u "${RPC_URL}" transfer \
    "${SUBMITTER_ACCOUNT}" \
    "${RETPAY_ACCOUNT}" \
    "${PRICE_SINGLE}" \
    "single|${SUBMITTER_ACCOUNT}|${SCHEMA_ID}|${POLICY_BATCH_ID}|$(hash_text "unified-retail-invalid-policy-${TIMESTAMP}")|$(hash_text "unified-retail-invalid-policy-ext-${TIMESTAMP}")" >/dev/null 2>&1; then
    echo "Assertion failed: atomic retail single transfer with invalid policy was accepted." >&2
    exit 1
fi

log "Funding unified retail transfer for duplicate request test"
cleos -u "${RPC_URL}" transfer \
    "${SUBMITTER_ACCOUNT}" \
    "${RETPAY_ACCOUNT}" \
    "${PRICE_SINGLE}" \
    "single|${SUBMITTER_ACCOUNT}|${SCHEMA_ID}|${POLICY_SINGLE_ID}|$(hash_text "unified-retail-object-mismatch-ok-${TIMESTAMP}")|${SINGLE_EXTREF_MISMATCH}"

log "Rejecting duplicate unified retail single submit"
if cleos -u "${RPC_URL}" transfer \
    "${SUBMITTER_ACCOUNT}" \
    "${RETPAY_ACCOUNT}" \
    "${PRICE_SINGLE}" \
    "single|${SUBMITTER_ACCOUNT}|${SCHEMA_ID}|${POLICY_SINGLE_ID}|$(hash_text "unified-retail-duplicate-${TIMESTAMP}")|${SINGLE_EXTREF}" >/dev/null 2>&1; then
    echo "Assertion failed: duplicate unified retail single request was accepted." >&2
    exit 1
fi

log "Funding unified retail batch transfer"
cleos -u "${RPC_URL}" transfer \
    "${SUBMITTER_ACCOUNT}" \
    "${RETPAY_ACCOUNT}" \
    "${PRICE_BATCH}" \
    "batch|${SUBMITTER_ACCOUNT}|${SCHEMA_ID}|${POLICY_BATCH_ID}|${BATCH_ROOT_HASH}|2|${MANIFEST_HASH}|${BATCH_EXTREF}"

BATCH_ID="$(get_batch_id_by_external_ref "${BATCH_EXTREF}")"
BATCH_SUBMITTER="$(get_table_json "${VERIFICATION_ACCOUNT}" "${VERIFICATION_ACCOUNT}" batches | "${JQ_BIN}" -r \
    --argjson id "${BATCH_ID}" '.rows[] | select(.id == $id) | .submitter')"
BATCH_MANIFEST="$(get_table_json "${VERIFICATION_ACCOUNT}" "${VERIFICATION_ACCOUNT}" batches | "${JQ_BIN}" -r \
    --argjson id "${BATCH_ID}" '.rows[] | select(.id == $id) | .manifest_hash')"
BATCH_BYTES="$(get_table_json "${VERIFICATION_ACCOUNT}" "${VERIFICATION_ACCOUNT}" batches | "${JQ_BIN}" -r \
    --argjson id "${BATCH_ID}" '.rows[] | select(.id == $id) | .billable_bytes')"
BATCH_BILLABLE_KIB="$(get_table_json "${VERIFICATION_ACCOUNT}" "${VERIFICATION_ACCOUNT}" batches | "${JQ_BIN}" -r \
    --argjson id "${BATCH_ID}" '.rows[] | select(.id == $id) | .billable_kib')"
assert_eq "${SUBMITTER_ACCOUNT}" "${BATCH_SUBMITTER}" "unified retail batch submitter"
assert_eq "${MANIFEST_HASH}" "${BATCH_MANIFEST}" "unified retail batch manifest hash"
assert_eq "${EXPECTED_BATCH_BYTES}" "${BATCH_BYTES}" "unified retail batch billable bytes"
assert_eq "${BATCH_KIB}" "${BATCH_BILLABLE_KIB}" "unified retail batch billable kib"

log "Unified retail smoke test passed"
