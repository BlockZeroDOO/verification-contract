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
PRICE_SINGLE="${PRICE_SINGLE:-0.0100 EOS}"
PRICE_BATCH="${PRICE_BATCH:-0.0200 EOS}"
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

get_rtlauth_id_by_external_ref() {
    local external_ref="$1"
    get_table_json "${RETPAY_ACCOUNT}" "${RETPAY_ACCOUNT}" rtlauths | "${JQ_BIN}" -r \
        --arg submitter "${SUBMITTER_ACCOUNT}" \
        --arg external_ref "${external_ref}" \
        '.rows[] | select(.submitter == $submitter and .external_ref == $external_ref) | .auth_id' | tail -n 1
}

assert_rtlauth_consumed() {
    local auth_id="$1"
    wait_for_table_match \
        "${RETPAY_ACCOUNT}" \
        "${RETPAY_ACCOUNT}" \
        "rtlauths" \
        ".rows[] | select(.auth_id == ${auth_id} and ((.consumed == true) or (.consumed == 1)))" \
        "consumed retail authorization ${auth_id}"
}

TIMESTAMP="$(date -u +%Y%m%d%H%M%S)"
BASE_ID="$(date -u +%s)"

SCHEMA_ID="${SCHEMA_ID:-$((BASE_ID + 5000))}"
POLICY_SINGLE_ID="${POLICY_SINGLE_ID:-$((BASE_ID + 6000))}"
POLICY_BATCH_ID="${POLICY_BATCH_ID:-$((BASE_ID + 6001))}"

SINGLE_EXTREF="$(hash_text "unified-retail-single-${TIMESTAMP}")"
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
    "[0,\"${PAYMENT_TOKEN_CONTRACT}\",\"${PRICE_SINGLE}\"]" \
    -p "${RETPAY_OWNER_ACCOUNT}@active"

log "Configuring retail batch tariff"
cleos -u "${RPC_URL}" push action "${RETPAY_ACCOUNT}" setprice \
    "[1,\"${PAYMENT_TOKEN_CONTRACT}\",\"${PRICE_BATCH}\"]" \
    -p "${RETPAY_OWNER_ACCOUNT}@active"

log "Creating unified retail schema"
cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" addschema \
    "[${SCHEMA_ID},\"1.0.0\",\"$(hash_text "unified-retail-schema-${TIMESTAMP}")\",\"$(hash_text "unified-retail-policy-${TIMESTAMP}")\"]" \
    -p "${OWNER_ACCOUNT}@active"

log "Creating unified retail single policy"
cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" setpolicy \
    "[${POLICY_SINGLE_ID},true,false,false,0,true]" \
    -p "${OWNER_ACCOUNT}@active"

log "Creating unified retail batch policy"
cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" setpolicy \
    "[${POLICY_BATCH_ID},false,true,false,0,true]" \
    -p "${OWNER_ACCOUNT}@active"

log "Funding unified retail single authorization"
cleos -u "${RPC_URL}" transfer \
    "${SUBMITTER_ACCOUNT}" \
    "${RETPAY_ACCOUNT}" \
    "${PRICE_SINGLE}" \
    "single|${SUBMITTER_ACCOUNT}|${SINGLE_EXTREF}"

wait_for_table_match \
    "${RETPAY_ACCOUNT}" \
    "${RETPAY_ACCOUNT}" \
    "rtlauths" \
    ".rows[] | select(.submitter == \"${SUBMITTER_ACCOUNT}\" and .external_ref == \"${SINGLE_EXTREF}\" and ((.consumed == false) or (.consumed == 0)))" \
    "retail single authorization"

SINGLE_AUTH_ID="$(get_rtlauth_id_by_external_ref "${SINGLE_EXTREF}")"

log "Submitting unified retail single commitment"
cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" submit \
    "[\"${SUBMITTER_ACCOUNT}\",${SCHEMA_ID},${POLICY_SINGLE_ID},\"${SINGLE_OBJECT_HASH}\",\"${SINGLE_EXTREF}\"]" \
    -p "${SUBMITTER_ACCOUNT}@active"

COMMITMENT_ID="$(get_commitment_id_by_external_ref "${SINGLE_EXTREF}")"
COMMITMENT_SUBMITTER="$(get_table_json "${VERIFICATION_ACCOUNT}" "${VERIFICATION_ACCOUNT}" commitments | "${JQ_BIN}" -r \
    --argjson id "${COMMITMENT_ID}" '.rows[] | select(.id == $id) | .submitter')"
COMMITMENT_STATUS="$(get_table_json "${VERIFICATION_ACCOUNT}" "${VERIFICATION_ACCOUNT}" commitments | "${JQ_BIN}" -r \
    --argjson id "${COMMITMENT_ID}" '.rows[] | select(.id == $id) | .status')"
assert_eq "${SUBMITTER_ACCOUNT}" "${COMMITMENT_SUBMITTER}" "unified retail commitment submitter"
assert_eq "0" "${COMMITMENT_STATUS}" "unified retail commitment status"
assert_rtlauth_consumed "${SINGLE_AUTH_ID}"

log "Rejecting duplicate unified retail single submit"
if cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" submit \
    "[\"${SUBMITTER_ACCOUNT}\",${SCHEMA_ID},${POLICY_SINGLE_ID},\"${SINGLE_OBJECT_HASH}\",\"${SINGLE_EXTREF}\"]" \
    -p "${SUBMITTER_ACCOUNT}@active" >/dev/null 2>&1; then
    echo "Assertion failed: duplicate unified retail single submit was accepted." >&2
    exit 1
fi

log "Funding unified retail batch authorization"
cleos -u "${RPC_URL}" transfer \
    "${SUBMITTER_ACCOUNT}" \
    "${RETPAY_ACCOUNT}" \
    "${PRICE_BATCH}" \
    "batch|${SUBMITTER_ACCOUNT}|${BATCH_EXTREF}"

wait_for_table_match \
    "${RETPAY_ACCOUNT}" \
    "${RETPAY_ACCOUNT}" \
    "rtlauths" \
    ".rows[] | select(.submitter == \"${SUBMITTER_ACCOUNT}\" and .external_ref == \"${BATCH_EXTREF}\" and .mode == 1 and ((.consumed == false) or (.consumed == 0)))" \
    "retail batch authorization"

BATCH_AUTH_ID="$(get_rtlauth_id_by_external_ref "${BATCH_EXTREF}")"

log "Submitting unified retail batch root"
cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" submitroot \
    "[\"${SUBMITTER_ACCOUNT}\",${SCHEMA_ID},${POLICY_BATCH_ID},\"${BATCH_ROOT_HASH}\",2,\"${BATCH_EXTREF}\"]" \
    -p "${SUBMITTER_ACCOUNT}@active"

BATCH_ID="$(get_batch_id_by_external_ref "${BATCH_EXTREF}")"
BATCH_SUBMITTER="$(get_table_json "${VERIFICATION_ACCOUNT}" "${VERIFICATION_ACCOUNT}" batches | "${JQ_BIN}" -r \
    --argjson id "${BATCH_ID}" '.rows[] | select(.id == $id) | .submitter')"
BATCH_STATUS="$(get_table_json "${VERIFICATION_ACCOUNT}" "${VERIFICATION_ACCOUNT}" batches | "${JQ_BIN}" -r \
    --argjson id "${BATCH_ID}" '.rows[] | select(.id == $id) | .status')"
assert_eq "${SUBMITTER_ACCOUNT}" "${BATCH_SUBMITTER}" "unified retail batch submitter"
assert_eq "0" "${BATCH_STATUS}" "unified retail batch status"
assert_rtlauth_consumed "${BATCH_AUTH_ID}"

log "Linking manifest for unified retail batch"
cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" linkmanifest \
    "[${BATCH_ID},\"${MANIFEST_HASH}\"]" \
    -p "${SUBMITTER_ACCOUNT}@active"

wait_for_table_match \
    "${VERIFICATION_ACCOUNT}" \
    "${VERIFICATION_ACCOUNT}" \
    "batches" \
    ".rows[] | select(.id == ${BATCH_ID} and .manifest_hash == \"${MANIFEST_HASH}\")" \
    "linked manifest for unified retail batch ${BATCH_ID}"

log "Closing unified retail batch"
cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" closebatch \
    "[${BATCH_ID}]" \
    -p "${SUBMITTER_ACCOUNT}@active"

FINAL_BATCH_STATUS="$(get_table_json "${VERIFICATION_ACCOUNT}" "${VERIFICATION_ACCOUNT}" batches | "${JQ_BIN}" -r \
    --argjson id "${BATCH_ID}" '.rows[] | select(.id == $id) | .status')"
assert_eq "1" "${FINAL_BATCH_STATUS}" "unified retail batch closed status"

log "Unified retail smoke test passed"
