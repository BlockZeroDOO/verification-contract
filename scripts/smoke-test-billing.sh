#!/usr/bin/env bash

set -euo pipefail

RPC_URL="${RPC_URL:-https://jungle4.api.eosnation.io}"
READ_RPC_URL="${READ_RPC_URL:-${RPC_URL}}"
BILLING_ACCOUNT="${BILLING_ACCOUNT:-verifbill}"
VERIFICATION_ACCOUNT="${VERIFICATION_ACCOUNT:-verif}"
OWNER_ACCOUNT="${OWNER_ACCOUNT:-}"
VERIFICATION_OWNER_ACCOUNT="${VERIFICATION_OWNER_ACCOUNT:-${VERIFICATION_ACCOUNT}}"
RETAIL_PAYMENT_ACCOUNT="${RETAIL_PAYMENT_ACCOUNT:-${BILLING_ACCOUNT}}"
PAYER_ACCOUNT="${PAYER_ACCOUNT:-}"
SUBMITTER_ACCOUNT="${SUBMITTER_ACCOUNT:-}"
PAYMENT_TOKEN_CONTRACT="${PAYMENT_TOKEN_CONTRACT:-eosio.token}"
PAYMENT_SYMBOL="${PAYMENT_SYMBOL:-EOS}"
PAYMENT_PRECISION="${PAYMENT_PRECISION:-4}"
PLAN_CODE="${PLAN_CODE:-}"
PACK_CODE="${PACK_CODE:-}"
PLAN_PRICE="${PLAN_PRICE:-0.0300 EOS}"
PACK_PRICE="${PACK_PRICE:-0.0200 EOS}"
PLAN_DURATION_SEC="${PLAN_DURATION_SEC:-2592000}"
PLAN_INCLUDED_KIB="${PLAN_INCLUDED_KIB:-8}"
PACK_INCLUDED_KIB="${PACK_INCLUDED_KIB:-6}"
BILLABLE_BYTES_SINGLE="${BILLABLE_BYTES_SINGLE:-1536}"
BILLABLE_BYTES_BATCH="${BILLABLE_BYTES_BATCH:-3072}"
WAIT_TIMEOUT_SEC="${WAIT_TIMEOUT_SEC:-90}"
WAIT_INTERVAL_SEC="${WAIT_INTERVAL_SEC:-1}"

: "${OWNER_ACCOUNT:?Set OWNER_ACCOUNT to the billing contract authority account.}"
: "${VERIFICATION_OWNER_ACCOUNT:?Set VERIFICATION_OWNER_ACCOUNT to the verif authority account.}"
: "${PAYER_ACCOUNT:?Set PAYER_ACCOUNT to a funded enterprise payer account.}"
: "${SUBMITTER_ACCOUNT:?Set SUBMITTER_ACCOUNT to the enterprise submitter account.}"

if [[ ${#BILLING_ACCOUNT} -gt 12 ]]; then
    echo "BILLING_ACCOUNT must be 12 characters or fewer for Antelope account names: ${BILLING_ACCOUNT}" >&2
    exit 1
fi

if ! command -v cleos >/dev/null 2>&1; then
    echo "cleos is required for smoke-test-billing.sh" >&2
    exit 1
fi

if command -v jq >/dev/null 2>&1; then
    JQ_BIN="jq"
else
    echo "jq is required for smoke-test-billing.sh" >&2
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

normalize_name_fragment() {
    local input="$1"
    printf '%s' "${input}" | tr '06789' 'abcde'
}

log() {
    printf '[smoke-test-billing] %s\n' "$1"
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
if [[ -z "${PLAN_CODE}" ]]; then
    PLAN_CODE="pl$(normalize_name_fragment "${TIMESTAMP:8:6}")"
fi
if [[ -z "${PACK_CODE}" ]]; then
    PACK_CODE="pk$(normalize_name_fragment "${TIMESTAMP:8:6}")"
fi

if [[ ${#PLAN_CODE} -gt 12 ]]; then
    echo "PLAN_CODE must be 12 characters or fewer: ${PLAN_CODE}" >&2
    exit 1
fi

if [[ ${#PACK_CODE} -gt 12 ]]; then
    echo "PACK_CODE must be 12 characters or fewer: ${PACK_CODE}" >&2
    exit 1
fi

SCHEMA_ID="${SCHEMA_ID:-$((BASE_ID + 1000))}"
POLICY_SINGLE_ID="${POLICY_SINGLE_ID:-$((BASE_ID + 2000))}"
POLICY_BATCH_ID="${POLICY_BATCH_ID:-$((BASE_ID + 2001))}"

COMMIT_EXTREF_SINGLE="$(hash_text "bill-single-${TIMESTAMP}")"
COMMIT_EXTREF_BATCH="$(hash_text "bill-batch-${TIMESTAMP}")"
COMMIT_EXTREF_DUPLICATE="$(hash_text "bill-duplicate-${TIMESTAMP}")"
OBJECT_HASH_SINGLE="$(hash_text "bill-object-single-${TIMESTAMP}")"
OBJECT_HASH_DUPLICATE="$(hash_text "bill-object-duplicate-${TIMESTAMP}")"
ROOT_HASH_BATCH="$(hash_text "bill-root-${TIMESTAMP}")"
MANIFEST_HASH_BATCH="$(hash_text "bill-manifest-${TIMESTAMP}")"
ZERO_HASH="$(printf '0%.0s' {1..64})"

EXPECTED_SINGLE_KIB="$(( (BILLABLE_BYTES_SINGLE + 1023) / 1024 ))"
EXPECTED_BATCH_KIB="$(( (BILLABLE_BYTES_BATCH + 1023) / 1024 ))"

log "Configuring verification authorization sources"
cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" setauthsrcs \
    "[\"${BILLING_ACCOUNT}\",\"${RETAIL_PAYMENT_ACCOUNT}\"]" \
    -p "${VERIFICATION_OWNER_ACCOUNT}@active"

log "Creating billing schema"
cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" addschema \
    "[${SCHEMA_ID},\"1.0.0\",\"$(hash_text "bill-schema-${TIMESTAMP}")\",\"$(hash_text "bill-schema-policy-${TIMESTAMP}")\"]" \
    -p "${VERIFICATION_OWNER_ACCOUNT}@active"

log "Creating billing single policy"
cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" setpolicy \
    "[${POLICY_SINGLE_ID},true,false,true]" \
    -p "${VERIFICATION_OWNER_ACCOUNT}@active"

log "Creating billing batch policy"
cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" setpolicy \
    "[${POLICY_BATCH_ID},false,true,true]" \
    -p "${VERIFICATION_OWNER_ACCOUNT}@active"

log "Configuring accepted billing token"
cleos -u "${RPC_URL}" push action "${BILLING_ACCOUNT}" settoken \
    "[\"${PAYMENT_TOKEN_CONTRACT}\",\"${PAYMENT_PRECISION},${PAYMENT_SYMBOL}\"]" \
    -p "${OWNER_ACCOUNT}@active"

log "Configuring verification account for billing orchestration"
cleos -u "${RPC_URL}" push action "${BILLING_ACCOUNT}" setverifacct \
    "[\"${VERIFICATION_ACCOUNT}\"]" \
    -p "${OWNER_ACCOUNT}@active"

log "Configuring enterprise plan"
cleos -u "${RPC_URL}" push action "${BILLING_ACCOUNT}" setplan \
    "[\"${PLAN_CODE}\",\"${PAYMENT_TOKEN_CONTRACT}\",\"${PLAN_PRICE}\",${PLAN_DURATION_SEC},${PLAN_INCLUDED_KIB},true]" \
    -p "${OWNER_ACCOUNT}@active"

log "Configuring enterprise pack"
cleos -u "${RPC_URL}" push action "${BILLING_ACCOUNT}" setpack \
    "[\"${PACK_CODE}\",\"${PAYMENT_TOKEN_CONTRACT}\",\"${PACK_PRICE}\",${PACK_INCLUDED_KIB},true]" \
    -p "${OWNER_ACCOUNT}@active"

log "Purchasing enterprise plan"
cleos -u "${RPC_URL}" transfer "${PAYER_ACCOUNT}" "${BILLING_ACCOUNT}" "${PLAN_PRICE}" \
    "plan|${PAYER_ACCOUNT}|${PLAN_CODE}"

wait_for_table_match \
    "${BILLING_ACCOUNT}" \
    "${BILLING_ACCOUNT}" \
    "entitlements" \
    ".rows[] | select(.payer == \"${PAYER_ACCOUNT}\" and .kind == 0)" \
    "plan entitlement for ${PAYER_ACCOUNT}"

log "Purchasing enterprise pack"
cleos -u "${RPC_URL}" transfer "${PAYER_ACCOUNT}" "${BILLING_ACCOUNT}" "${PACK_PRICE}" \
    "pack|${PAYER_ACCOUNT}|${PACK_CODE}"

wait_for_table_match \
    "${BILLING_ACCOUNT}" \
    "${BILLING_ACCOUNT}" \
    "entitlements" \
    ".rows[] | select(.payer == \"${PAYER_ACCOUNT}\" and .kind == 1)" \
    "pack entitlement for ${PAYER_ACCOUNT}"

PLAN_ENTITLEMENT_ID="$(get_table_json "${BILLING_ACCOUNT}" "${BILLING_ACCOUNT}" entitlements | "${JQ_BIN}" -r \
    --arg payer "${PAYER_ACCOUNT}" \
    '.rows[] | select(.payer == $payer and .kind == 0) | .entitlement_id' | tail -n 1)"
PLAN_KIB_BEFORE_SINGLE="$(get_table_json "${BILLING_ACCOUNT}" "${BILLING_ACCOUNT}" entitlements | "${JQ_BIN}" -r \
    --argjson id "${PLAN_ENTITLEMENT_ID}" \
    '.rows[] | select(.entitlement_id == $id) | .kib_remaining')"

log "Rejecting enterprise submit with mismatched payer and submitter"
if cleos -u "${RPC_URL}" push action "${BILLING_ACCOUNT}" submit \
    "[\"${PAYER_ACCOUNT}\",\"${OWNER_ACCOUNT}\",${SCHEMA_ID},${POLICY_SINGLE_ID},\"$(hash_text "bill-mismatch-object-${TIMESTAMP}")\",\"$(hash_text "bill-mismatch-ext-${TIMESTAMP}")\",${BILLABLE_BYTES_SINGLE}]" \
    -p "${PAYER_ACCOUNT}@active" >/dev/null 2>&1; then
    echo "Assertion failed: enterprise submit with mismatched payer/submitter was accepted." >&2
    exit 1
fi

log "Submitting atomic enterprise single record"
cleos -u "${RPC_URL}" push action "${BILLING_ACCOUNT}" submit \
    "[\"${PAYER_ACCOUNT}\",\"${SUBMITTER_ACCOUNT}\",${SCHEMA_ID},${POLICY_SINGLE_ID},\"${OBJECT_HASH_SINGLE}\",\"${COMMIT_EXTREF_SINGLE}\",${BILLABLE_BYTES_SINGLE}]" \
    -p "${PAYER_ACCOUNT}@active"

wait_for_table_match \
    "${VERIFICATION_ACCOUNT}" \
    "${VERIFICATION_ACCOUNT}" \
    "commitments" \
    ".rows[] | select(.external_ref == \"${COMMIT_EXTREF_SINGLE}\")" \
    "enterprise commitment ${COMMIT_EXTREF_SINGLE}"

COMMITMENT_ID="$(get_table_json "${VERIFICATION_ACCOUNT}" "${VERIFICATION_ACCOUNT}" commitments | "${JQ_BIN}" -r \
    --arg external_ref "${COMMIT_EXTREF_SINGLE}" \
    '.rows[] | select(.external_ref == $external_ref) | .id' | tail -n 1)"
COMMITMENT_BYTES="$(get_table_json "${VERIFICATION_ACCOUNT}" "${VERIFICATION_ACCOUNT}" commitments | "${JQ_BIN}" -r \
    --argjson id "${COMMITMENT_ID}" \
    '.rows[] | select(.id == $id) | .billable_bytes')"
COMMITMENT_KIB="$(get_table_json "${VERIFICATION_ACCOUNT}" "${VERIFICATION_ACCOUNT}" commitments | "${JQ_BIN}" -r \
    --argjson id "${COMMITMENT_ID}" \
    '.rows[] | select(.id == $id) | .billable_kib')"
assert_eq "${BILLABLE_BYTES_SINGLE}" "${COMMITMENT_BYTES}" "enterprise commitment billable bytes"
assert_eq "${EXPECTED_SINGLE_KIB}" "${COMMITMENT_KIB}" "enterprise commitment billable kib"

PLAN_KIB_AFTER_SINGLE="$(get_table_json "${BILLING_ACCOUNT}" "${BILLING_ACCOUNT}" entitlements | "${JQ_BIN}" -r \
    --argjson id "${PLAN_ENTITLEMENT_ID}" \
    '.rows[] | select(.entitlement_id == $id) | .kib_remaining')"
assert_eq "$(( PLAN_KIB_BEFORE_SINGLE - EXPECTED_SINGLE_KIB ))" "${PLAN_KIB_AFTER_SINGLE}" "nearest-expiry plan entitlement usage"

log "Rejecting duplicate enterprise single request"
if cleos -u "${RPC_URL}" push action "${BILLING_ACCOUNT}" submit \
    "[\"${PAYER_ACCOUNT}\",\"${SUBMITTER_ACCOUNT}\",${SCHEMA_ID},${POLICY_SINGLE_ID},\"${OBJECT_HASH_DUPLICATE}\",\"${COMMIT_EXTREF_SINGLE}\",${BILLABLE_BYTES_SINGLE}]" \
    -p "${PAYER_ACCOUNT}@active" >/dev/null 2>&1; then
    echo "Assertion failed: duplicate enterprise single request was accepted." >&2
    exit 1
fi

MAX_LIVE_KIB="$(get_table_json "${BILLING_ACCOUNT}" "${BILLING_ACCOUNT}" entitlements | "${JQ_BIN}" -r \
    --arg payer "${PAYER_ACCOUNT}" \
    '[.rows[] | select(.payer == $payer and .status == 0) | .kib_remaining] | max // 0')"
TOO_LARGE_BYTES="$(( (MAX_LIVE_KIB + 1) * 1024 ))"
log "Rejecting oversized enterprise request"
if cleos -u "${RPC_URL}" push action "${BILLING_ACCOUNT}" submit \
    "[\"${PAYER_ACCOUNT}\",\"${SUBMITTER_ACCOUNT}\",${SCHEMA_ID},${POLICY_SINGLE_ID},\"$(hash_text "bill-too-large-object-${TIMESTAMP}")\",\"${COMMIT_EXTREF_DUPLICATE}\",${TOO_LARGE_BYTES}]" \
    -p "${PAYER_ACCOUNT}@active" >/dev/null 2>&1; then
    echo "Assertion failed: oversized enterprise request was accepted." >&2
    exit 1
fi

log "Rejecting zero object hash"
if cleos -u "${RPC_URL}" push action "${BILLING_ACCOUNT}" submit \
    "[\"${PAYER_ACCOUNT}\",\"${SUBMITTER_ACCOUNT}\",${SCHEMA_ID},${POLICY_SINGLE_ID},\"${ZERO_HASH}\",\"$(hash_text "bill-zero-hash-${TIMESTAMP}")\",${BILLABLE_BYTES_SINGLE}]" \
    -p "${PAYER_ACCOUNT}@active" >/dev/null 2>&1; then
    echo "Assertion failed: zero object hash was accepted." >&2
    exit 1
fi

log "Submitting atomic enterprise batch"
cleos -u "${RPC_URL}" push action "${BILLING_ACCOUNT}" submitroot \
    "[\"${PAYER_ACCOUNT}\",\"${SUBMITTER_ACCOUNT}\",${SCHEMA_ID},${POLICY_BATCH_ID},\"${ROOT_HASH_BATCH}\",2,\"${MANIFEST_HASH_BATCH}\",\"${COMMIT_EXTREF_BATCH}\",${BILLABLE_BYTES_BATCH}]" \
    -p "${PAYER_ACCOUNT}@active"

wait_for_table_match \
    "${VERIFICATION_ACCOUNT}" \
    "${VERIFICATION_ACCOUNT}" \
    "batches" \
    ".rows[] | select(.external_ref == \"${COMMIT_EXTREF_BATCH}\")" \
    "enterprise batch ${COMMIT_EXTREF_BATCH}"

BATCH_ID="$(get_table_json "${VERIFICATION_ACCOUNT}" "${VERIFICATION_ACCOUNT}" batches | "${JQ_BIN}" -r \
    --arg external_ref "${COMMIT_EXTREF_BATCH}" \
    '.rows[] | select(.external_ref == $external_ref) | .id' | tail -n 1)"
BATCH_BYTES="$(get_table_json "${VERIFICATION_ACCOUNT}" "${VERIFICATION_ACCOUNT}" batches | "${JQ_BIN}" -r \
    --argjson id "${BATCH_ID}" \
    '.rows[] | select(.id == $id) | .billable_bytes')"
BATCH_KIB="$(get_table_json "${VERIFICATION_ACCOUNT}" "${VERIFICATION_ACCOUNT}" batches | "${JQ_BIN}" -r \
    --argjson id "${BATCH_ID}" \
    '.rows[] | select(.id == $id) | .billable_kib')"
assert_eq "${BILLABLE_BYTES_BATCH}" "${BATCH_BYTES}" "enterprise batch billable bytes"
assert_eq "${EXPECTED_BATCH_KIB}" "${BATCH_KIB}" "enterprise batch billable kib"

log "Enterprise billing smoke test passed"
