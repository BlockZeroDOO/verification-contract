#!/usr/bin/env bash

set -euo pipefail

RPC_URL="${RPC_URL:-https://history.denotary.io}"
READ_RPC_URL="${READ_RPC_URL:-${RPC_URL}}"
VERIFICATION_ACCOUNT="${VERIFICATION_ACCOUNT:-verif}"
VERIFICATION_BILLING_ACCOUNT="${VERIFICATION_BILLING_ACCOUNT:-verifbill}"
SUBMITTER_ACCOUNT="${SUBMITTER_ACCOUNT:-}"
BILLING_OWNER_ACCOUNT="${BILLING_OWNER_ACCOUNT:-${VERIFICATION_BILLING_ACCOUNT}}"
WAIT_TIMEOUT_SEC="${WAIT_TIMEOUT_SEC:-90}"
WAIT_INTERVAL_SEC="${WAIT_INTERVAL_SEC:-1}"
PAYMENT_TOKEN_CONTRACT="${PAYMENT_TOKEN_CONTRACT:-eosio.token}"
PAYMENT_SYMBOL="${PAYMENT_SYMBOL:-EOS}"
PAYMENT_PRECISION="${PAYMENT_PRECISION:-4}"
ENTERPRISE_PACK_CODE="${ENTERPRISE_PACK_CODE:-}"
ENTERPRISE_PACK_PRICE="${ENTERPRISE_PACK_PRICE:-0.0500 EOS}"
ENTERPRISE_PACK_INCLUDED_KIB="${ENTERPRISE_PACK_INCLUDED_KIB:-12}"

: "${SUBMITTER_ACCOUNT:?Set SUBMITTER_ACCOUNT to a funded test account that can sign submits.}"
: "${BILLING_OWNER_ACCOUNT:?Set BILLING_OWNER_ACCOUNT to the verifbill authority account.}"

if ! command -v cleos >/dev/null 2>&1; then
    echo "cleos is required for smoke-test-onchain.sh" >&2
    exit 1
fi

if command -v jq >/dev/null 2>&1; then
    JQ_BIN="jq"
else
    echo "jq is required for smoke-test-onchain.sh" >&2
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
    printf '[smoke-test-onchain] %s\n' "$1"
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

wait_for_table_field_eq() {
    local code="$1"
    local scope="$2"
    local table="$3"
    local row_id="$4"
    local field_name="$5"
    local expected="$6"
    local description="$7"

    local deadline=$(( $(date -u +%s) + WAIT_TIMEOUT_SEC ))
    while true; do
        if get_table_json "${code}" "${scope}" "${table}" | "${JQ_BIN}" -e \
            --argjson id "${row_id}" \
            --arg field "${field_name}" \
            --arg expected "${expected}" \
            '.rows[] | select(.id == $id) | .[$field] | tostring == $expected' >/dev/null 2>&1; then
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

assert_commitment_field() {
    local commitment_id="$1"
    local field_name="$2"
    local expected="$3"

    wait_for_table_field_eq \
        "${VERIFICATION_ACCOUNT}" \
        "${VERIFICATION_ACCOUNT}" \
        "commitments" \
        "${commitment_id}" \
        "${field_name}" \
        "${expected}" \
        "commitment ${commitment_id} field ${field_name} == ${expected}"

    local actual
    actual="$(get_table_json "${VERIFICATION_ACCOUNT}" "${VERIFICATION_ACCOUNT}" commitments | "${JQ_BIN}" -r \
        --argjson id "${commitment_id}" \
        --arg field "${field_name}" \
        '.rows[] | select(.id == $id) | .[$field]')"

    assert_eq "${expected}" "${actual}" "commitment ${commitment_id} field ${field_name}"
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

assert_batch_field() {
    local batch_id="$1"
    local field_name="$2"
    local expected="$3"

    wait_for_table_field_eq \
        "${VERIFICATION_ACCOUNT}" \
        "${VERIFICATION_ACCOUNT}" \
        "batches" \
        "${batch_id}" \
        "${field_name}" \
        "${expected}" \
        "batch ${batch_id} field ${field_name} == ${expected}"

    local actual
    actual="$(get_table_json "${VERIFICATION_ACCOUNT}" "${VERIFICATION_ACCOUNT}" batches | "${JQ_BIN}" -r \
        --argjson id "${batch_id}" \
        --arg field "${field_name}" \
        '.rows[] | select(.id == $id) | .[$field]')"

    assert_eq "${expected}" "${actual}" "batch ${batch_id} field ${field_name}"
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
if [[ -z "${ENTERPRISE_PACK_CODE}" ]]; then
    ENTERPRISE_PACK_CODE="ep$(normalize_name_fragment "${TIMESTAMP:8:6}")"
fi
if [[ ${#ENTERPRISE_PACK_CODE} -gt 12 ]]; then
    echo "ENTERPRISE_PACK_CODE must be 12 characters or fewer: ${ENTERPRISE_PACK_CODE}" >&2
    exit 1
fi

SCHEMA_ID="${SCHEMA_ID:-}"
POLICY_SINGLE_ID="${POLICY_SINGLE_ID:-}"
POLICY_BATCH_ID="${POLICY_BATCH_ID:-}"
: "${SCHEMA_ID:?Set SCHEMA_ID to an existing verif schema row.}"
: "${POLICY_SINGLE_ID:?Set POLICY_SINGLE_ID to an existing single-submit policy row.}"
: "${POLICY_BATCH_ID:?Set POLICY_BATCH_ID to an existing batch-submit policy row.}"

COMMIT_EXTREF_1="$(hash_text "commit-1-${TIMESTAMP}")"
COMMIT_EXTREF_2="$(hash_text "commit-2-${TIMESTAMP}")"
COMMIT_EXTREF_MISMATCH="$(hash_text "commit-mismatch-${TIMESTAMP}")"

OBJECT_HASH_1="$(hash_text "object-1-${TIMESTAMP}")"
OBJECT_HASH_2="$(hash_text "object-2-${TIMESTAMP}")"
ZERO_HASH="$(printf '0%.0s' {1..64})"

BATCH_EXTREF="$(hash_text "batch-${TIMESTAMP}")"
ROOT_HASH="$(hash_text "root-${TIMESTAMP}")"
MANIFEST_HASH="$(hash_text "manifest-${TIMESTAMP}")"
EXPECTED_SINGLE_BYTES=88
EXPECTED_BATCH_BYTES=124
EXPECTED_SINGLE_KIB="$(( (EXPECTED_SINGLE_BYTES + 1023) / 1024 ))"
EXPECTED_BATCH_KIB="$(( (EXPECTED_BATCH_BYTES + 1023) / 1024 ))"

wait_for_table_match \
    "${VERIFICATION_ACCOUNT}" \
    "${VERIFICATION_ACCOUNT}" \
    "schemas" \
    ".rows[] | select(.id == ${SCHEMA_ID})" \
    "schema ${SCHEMA_ID}"

wait_for_table_match \
    "${VERIFICATION_ACCOUNT}" \
    "${VERIFICATION_ACCOUNT}" \
    "policies" \
    ".rows[] | select(.id == ${POLICY_SINGLE_ID})" \
    "policy ${POLICY_SINGLE_ID}"

wait_for_table_match \
    "${VERIFICATION_ACCOUNT}" \
    "${VERIFICATION_ACCOUNT}" \
    "policies" \
    ".rows[] | select(.id == ${POLICY_BATCH_ID})" \
    "policy ${POLICY_BATCH_ID}"

log "Configuring enterprise billing token"
cleos -u "${RPC_URL}" push action "${VERIFICATION_BILLING_ACCOUNT}" settoken \
    "[\"${PAYMENT_TOKEN_CONTRACT}\",\"${PAYMENT_PRECISION},${PAYMENT_SYMBOL}\"]" \
    -p "${BILLING_OWNER_ACCOUNT}@active"

log "Configuring verification account for contract-only enterprise flow"
cleos -u "${RPC_URL}" push action "${VERIFICATION_BILLING_ACCOUNT}" setverifacct \
    "[\"${VERIFICATION_ACCOUNT}\"]" \
    -p "${BILLING_OWNER_ACCOUNT}@active"

log "Configuring enterprise billing pack"
cleos -u "${RPC_URL}" push action "${VERIFICATION_BILLING_ACCOUNT}" setpack \
    "[\"${ENTERPRISE_PACK_CODE}\",\"${PAYMENT_TOKEN_CONTRACT}\",\"${ENTERPRISE_PACK_PRICE}\",${ENTERPRISE_PACK_INCLUDED_KIB},true]" \
    -p "${BILLING_OWNER_ACCOUNT}@active"

log "Funding enterprise billing entitlement"
cleos -u "${RPC_URL}" transfer \
    "${SUBMITTER_ACCOUNT}" \
    "${VERIFICATION_BILLING_ACCOUNT}" \
    "${ENTERPRISE_PACK_PRICE}" \
    "pack|${SUBMITTER_ACCOUNT}|${ENTERPRISE_PACK_CODE}"

log "Submitting commitment #1"
cleos -u "${RPC_URL}" push action "${VERIFICATION_BILLING_ACCOUNT}" submit \
    "[\"${SUBMITTER_ACCOUNT}\",\"${SUBMITTER_ACCOUNT}\",${SCHEMA_ID},${POLICY_SINGLE_ID},\"${OBJECT_HASH_1}\",\"${COMMIT_EXTREF_1}\"]" \
    -p "${SUBMITTER_ACCOUNT}@active"
COMMITMENT_ID_1="$(get_commitment_id_by_external_ref "${COMMIT_EXTREF_1}")"
assert_commitment_field "${COMMITMENT_ID_1}" "submitter" "${SUBMITTER_ACCOUNT}"
assert_commitment_field "${COMMITMENT_ID_1}" "billable_bytes" "${EXPECTED_SINGLE_BYTES}"
assert_commitment_field "${COMMITMENT_ID_1}" "billable_kib" "${EXPECTED_SINGLE_KIB}"

log "Rejecting contract-only enterprise submit with mismatched payer and submitter"
if cleos -u "${RPC_URL}" push action "${VERIFICATION_BILLING_ACCOUNT}" submit \
    "[\"${SUBMITTER_ACCOUNT}\",\"${VERIFICATION_ACCOUNT}\",${SCHEMA_ID},${POLICY_SINGLE_ID},\"$(hash_text "object-mismatch-${TIMESTAMP}")\",\"${COMMIT_EXTREF_MISMATCH}\"]" \
    -p "${SUBMITTER_ACCOUNT}@active" >/dev/null 2>&1; then
    echo "Assertion failed: contract-only enterprise submit with mismatched payer/submitter was accepted." >&2
    exit 1
fi

log "Submitting enterprise commitment through contract-only path"
cleos -u "${RPC_URL}" push action "${VERIFICATION_BILLING_ACCOUNT}" submit \
    "[\"${SUBMITTER_ACCOUNT}\",\"${SUBMITTER_ACCOUNT}\",${SCHEMA_ID},${POLICY_SINGLE_ID},\"$(hash_text "object-mismatch-ok-${TIMESTAMP}")\",\"${COMMIT_EXTREF_MISMATCH}\"]" \
    -p "${SUBMITTER_ACCOUNT}@active"

log "Rejecting duplicate commitment request"
if cleos -u "${RPC_URL}" push action "${VERIFICATION_BILLING_ACCOUNT}" submit \
    "[\"${SUBMITTER_ACCOUNT}\",\"${SUBMITTER_ACCOUNT}\",${SCHEMA_ID},${POLICY_SINGLE_ID},\"${OBJECT_HASH_1}\",\"${COMMIT_EXTREF_1}\"]" \
    -p "${SUBMITTER_ACCOUNT}@active" >/dev/null 2>&1; then
    echo "Assertion failed: duplicate commitment request was accepted." >&2
    exit 1
fi

log "Rejecting zero object_hash commitment"
if cleos -u "${RPC_URL}" push action "${VERIFICATION_BILLING_ACCOUNT}" submit \
    "[\"${SUBMITTER_ACCOUNT}\",\"${SUBMITTER_ACCOUNT}\",${SCHEMA_ID},${POLICY_SINGLE_ID},\"${ZERO_HASH}\",\"$(hash_text "zero-hash-${TIMESTAMP}")\"]" \
    -p "${SUBMITTER_ACCOUNT}@active" >/dev/null 2>&1; then
    echo "Assertion failed: zero object_hash commitment was accepted." >&2
    exit 1
fi

log "Submitting successor commitment #2"
cleos -u "${RPC_URL}" push action "${VERIFICATION_BILLING_ACCOUNT}" submit \
    "[\"${SUBMITTER_ACCOUNT}\",\"${SUBMITTER_ACCOUNT}\",${SCHEMA_ID},${POLICY_SINGLE_ID},\"${OBJECT_HASH_2}\",\"${COMMIT_EXTREF_2}\"]" \
    -p "${SUBMITTER_ACCOUNT}@active"
COMMITMENT_ID_2="$(get_commitment_id_by_external_ref "${COMMIT_EXTREF_2}")"
assert_commitment_field "${COMMITMENT_ID_2}" "billable_bytes" "${EXPECTED_SINGLE_BYTES}"
assert_commitment_field "${COMMITMENT_ID_2}" "billable_kib" "${EXPECTED_SINGLE_KIB}"

log "Submitting batch #1 through contract-only path"
cleos -u "${RPC_URL}" push action "${VERIFICATION_BILLING_ACCOUNT}" submitroot \
    "[\"${SUBMITTER_ACCOUNT}\",\"${SUBMITTER_ACCOUNT}\",${SCHEMA_ID},${POLICY_BATCH_ID},\"${ROOT_HASH}\",2,\"${MANIFEST_HASH}\",\"${BATCH_EXTREF}\"]" \
    -p "${SUBMITTER_ACCOUNT}@active"
BATCH_ID_1="$(get_batch_id_by_external_ref "${BATCH_EXTREF}")"
assert_batch_field "${BATCH_ID_1}" "submitter" "${SUBMITTER_ACCOUNT}"
assert_batch_field "${BATCH_ID_1}" "manifest_hash" "${MANIFEST_HASH}"
assert_batch_field "${BATCH_ID_1}" "billable_bytes" "${EXPECTED_BATCH_BYTES}"
assert_batch_field "${BATCH_ID_1}" "billable_kib" "${EXPECTED_BATCH_KIB}"

log "Rejecting duplicate batch request"
if cleos -u "${RPC_URL}" push action "${VERIFICATION_BILLING_ACCOUNT}" submitroot \
    "[\"${SUBMITTER_ACCOUNT}\",\"${SUBMITTER_ACCOUNT}\",${SCHEMA_ID},${POLICY_BATCH_ID},\"${ROOT_HASH}\",2,\"${MANIFEST_HASH}\",\"${BATCH_EXTREF}\"]" \
    -p "${SUBMITTER_ACCOUNT}@active" >/dev/null 2>&1; then
    echo "Assertion failed: duplicate batch request was accepted." >&2
    exit 1
fi

log "On-chain smoke test passed"
