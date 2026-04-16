#!/usr/bin/env bash

set -euo pipefail

RPC_URL="${RPC_URL:-https://history.denotary.io}"
READ_RPC_URL="${READ_RPC_URL:-${RPC_URL}}"
VERIFICATION_ACCOUNT="${VERIFICATION_ACCOUNT:-verif}"
VERIFICATION_BILLING_ACCOUNT="${VERIFICATION_BILLING_ACCOUNT:-verifbill}"
SUBMITTER_ACCOUNT="${SUBMITTER_ACCOUNT:-}"
OWNER_ACCOUNT="${OWNER_ACCOUNT:-}"
BILLING_OWNER_ACCOUNT="${BILLING_OWNER_ACCOUNT:-${VERIFICATION_BILLING_ACCOUNT}}"
KYC_PROVIDER="${KYC_PROVIDER:-denotary-kyc}"
KYC_JURISDICTION="${KYC_JURISDICTION:-EU}"
KYC_LEVEL="${KYC_LEVEL:-2}"
KYC_EXPIRES_AT="${KYC_EXPIRES_AT:-2030-01-01T00:00:00}"
WAIT_TIMEOUT_SEC="${WAIT_TIMEOUT_SEC:-90}"
WAIT_INTERVAL_SEC="${WAIT_INTERVAL_SEC:-1}"
PAYMENT_TOKEN_CONTRACT="${PAYMENT_TOKEN_CONTRACT:-eosio.token}"
PAYMENT_SYMBOL="${PAYMENT_SYMBOL:-EOS}"
PAYMENT_PRECISION="${PAYMENT_PRECISION:-4}"
ENTERPRISE_PACK_CODE="${ENTERPRISE_PACK_CODE:-smokepack}"
ENTERPRISE_PACK_PRICE="${ENTERPRISE_PACK_PRICE:-0.0500 EOS}"
ENTERPRISE_PACK_SINGLE_UNITS="${ENTERPRISE_PACK_SINGLE_UNITS:-4}"
ENTERPRISE_PACK_BATCH_UNITS="${ENTERPRISE_PACK_BATCH_UNITS:-1}"

: "${OWNER_ACCOUNT:?Set OWNER_ACCOUNT to the enterprise contract authority account.}"
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

log() {
    printf '[smoke-test-onchain] %s\n' "$1"
}

enterprise_use() {
    local mode="$1"
    local external_ref="$2"
    cleos -u "${RPC_URL}" push action "${VERIFICATION_BILLING_ACCOUNT}" use \
        "[\"${SUBMITTER_ACCOUNT}\",\"${SUBMITTER_ACCOUNT}\",${mode},\"${external_ref}\"]" \
        -p "${SUBMITTER_ACCOUNT}@active"
}

get_table_json() {
    local code="$1"
    local scope="$2"
    local table="$3"
    cleos -u "${READ_RPC_URL}" get table "${code}" "${scope}" "${table}" --limit 1000
}

kyc_row_exists() {
    get_table_json "${VERIFICATION_ACCOUNT}" "${VERIFICATION_ACCOUNT}" "kyc" | "${JQ_BIN}" -e \
        --arg account "${SUBMITTER_ACCOUNT}" \
        '.rows[] | select(.account == $account)' >/dev/null 2>&1
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

SCHEMA_ID="${SCHEMA_ID:-$((BASE_ID + 1000))}"
POLICY_SINGLE_ID="${POLICY_SINGLE_ID:-$((BASE_ID + 2000))}"
POLICY_BATCH_ID="${POLICY_BATCH_ID:-$((BASE_ID + 2001))}"

COMMIT_EXTREF_1="$(hash_text "commit-1-${TIMESTAMP}")"
COMMIT_EXTREF_2="$(hash_text "commit-2-${TIMESTAMP}")"
COMMIT_EXTREF_3="$(hash_text "commit-3-${TIMESTAMP}")"
COMMIT_EXTREF_4="$(hash_text "commit-4-${TIMESTAMP}")"

OBJECT_HASH_1="$(hash_text "object-1-${TIMESTAMP}")"
OBJECT_HASH_2="$(hash_text "object-2-${TIMESTAMP}")"
OBJECT_HASH_3="$(hash_text "object-3-${TIMESTAMP}")"
OBJECT_HASH_4="$(hash_text "object-4-${TIMESTAMP}")"
ZERO_HASH="$(printf '0%.0s' {1..64})"

BATCH_EXTREF="$(hash_text "batch-${TIMESTAMP}")"
ROOT_HASH="$(hash_text "root-${TIMESTAMP}")"
MANIFEST_HASH="$(hash_text "manifest-${TIMESTAMP}")"

if kyc_row_exists; then
    log "KYC row already exists for submitter; skipping issue"
else
    log "Creating KYC row for submitter"
    cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" issuekyc \
        "[\"${SUBMITTER_ACCOUNT}\",${KYC_LEVEL},\"${KYC_PROVIDER}\",\"${KYC_JURISDICTION}\",\"${KYC_EXPIRES_AT}\"]" \
        -p "${OWNER_ACCOUNT}@active"
    wait_for_table_match \
        "${VERIFICATION_ACCOUNT}" \
        "${VERIFICATION_ACCOUNT}" \
        "kyc" \
        ".rows[] | select(.account == \"${SUBMITTER_ACCOUNT}\")" \
        "kyc row for ${SUBMITTER_ACCOUNT}"
fi

log "Renewing KYC row"
cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" renewkyc \
    "[\"${SUBMITTER_ACCOUNT}\",\"${KYC_EXPIRES_AT}\"]" \
    -p "${OWNER_ACCOUNT}@active"

log "Creating schema"
cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" addschema \
    "[${SCHEMA_ID},\"1.0.0\",\"$(hash_text "schema-rules-${TIMESTAMP}")\",\"$(hash_text "hash-policy-${TIMESTAMP}")\"]" \
    -p "${OWNER_ACCOUNT}@active"
wait_for_table_match \
    "${VERIFICATION_ACCOUNT}" \
    "${VERIFICATION_ACCOUNT}" \
    "schemas" \
    ".rows[] | select(.id == ${SCHEMA_ID})" \
    "schema ${SCHEMA_ID}"

log "Creating single-submit policy"
cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" setpolicy \
    "[${POLICY_SINGLE_ID},true,false,true,${KYC_LEVEL},true]" \
    -p "${OWNER_ACCOUNT}@active"
wait_for_table_match \
    "${VERIFICATION_ACCOUNT}" \
    "${VERIFICATION_ACCOUNT}" \
    "policies" \
    ".rows[] | select(.id == ${POLICY_SINGLE_ID})" \
    "policy ${POLICY_SINGLE_ID}"

log "Creating batch-submit policy"
cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" setpolicy \
    "[${POLICY_BATCH_ID},false,true,false,0,true]" \
    -p "${OWNER_ACCOUNT}@active"
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

log "Configuring enterprise billing pack"
cleos -u "${RPC_URL}" push action "${VERIFICATION_BILLING_ACCOUNT}" setpack \
    "[\"${ENTERPRISE_PACK_CODE}\",\"${PAYMENT_TOKEN_CONTRACT}\",\"${ENTERPRISE_PACK_PRICE}\",${ENTERPRISE_PACK_SINGLE_UNITS},${ENTERPRISE_PACK_BATCH_UNITS},true]" \
    -p "${BILLING_OWNER_ACCOUNT}@active"

log "Funding enterprise billing entitlement"
cleos -u "${RPC_URL}" transfer \
    "${SUBMITTER_ACCOUNT}" \
    "${VERIFICATION_BILLING_ACCOUNT}" \
    "${ENTERPRISE_PACK_PRICE}" \
    "pack|${SUBMITTER_ACCOUNT}|${ENTERPRISE_PACK_CODE}"

log "Submitting commitment #1"
enterprise_use 0 "${COMMIT_EXTREF_1}"
cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" submit \
    "[\"${SUBMITTER_ACCOUNT}\",${SCHEMA_ID},${POLICY_SINGLE_ID},\"${OBJECT_HASH_1}\",\"${COMMIT_EXTREF_1}\"]" \
    -p "${SUBMITTER_ACCOUNT}@active"
COMMITMENT_ID_1="$(get_commitment_id_by_external_ref "${COMMIT_EXTREF_1}")"
assert_commitment_field "${COMMITMENT_ID_1}" "submitter" "${SUBMITTER_ACCOUNT}"
assert_commitment_field "${COMMITMENT_ID_1}" "status" "0"

log "Rejecting duplicate commitment request"
if cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" submit \
    "[\"${SUBMITTER_ACCOUNT}\",${SCHEMA_ID},${POLICY_SINGLE_ID},\"${OBJECT_HASH_1}\",\"${COMMIT_EXTREF_1}\"]" \
    -p "${SUBMITTER_ACCOUNT}@active" >/dev/null 2>&1; then
    echo "Assertion failed: duplicate commitment request was accepted." >&2
    exit 1
fi

log "Rejecting zero object_hash commitment"
if cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" submit \
    "[\"${SUBMITTER_ACCOUNT}\",${SCHEMA_ID},${POLICY_SINGLE_ID},\"${ZERO_HASH}\",\"$(hash_text "zero-hash-${TIMESTAMP}")\"]" \
    -p "${SUBMITTER_ACCOUNT}@active" >/dev/null 2>&1; then
    echo "Assertion failed: zero object_hash commitment was accepted." >&2
    exit 1
fi

log "Submitting successor commitment #2"
enterprise_use 0 "${COMMIT_EXTREF_2}"
cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" submit \
    "[\"${SUBMITTER_ACCOUNT}\",${SCHEMA_ID},${POLICY_SINGLE_ID},\"${OBJECT_HASH_2}\",\"${COMMIT_EXTREF_2}\"]" \
    -p "${SUBMITTER_ACCOUNT}@active"
COMMITMENT_ID_2="$(get_commitment_id_by_external_ref "${COMMIT_EXTREF_2}")"

log "Superseding commitment #1 with #2"
cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" supersede \
    "[${COMMITMENT_ID_1},${COMMITMENT_ID_2}]" \
    -p "${SUBMITTER_ACCOUNT}@active"
assert_commitment_field "${COMMITMENT_ID_1}" "status" "1"
assert_commitment_field "${COMMITMENT_ID_1}" "superseded_by" "${COMMITMENT_ID_2}"
assert_commitment_field "${COMMITMENT_ID_2}" "status" "0"

log "Submitting commitment #3 for revoke path"
enterprise_use 0 "${COMMIT_EXTREF_3}"
cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" submit \
    "[\"${SUBMITTER_ACCOUNT}\",${SCHEMA_ID},${POLICY_SINGLE_ID},\"${OBJECT_HASH_3}\",\"${COMMIT_EXTREF_3}\"]" \
    -p "${SUBMITTER_ACCOUNT}@active"
COMMITMENT_ID_3="$(get_commitment_id_by_external_ref "${COMMIT_EXTREF_3}")"
cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" revokecmmt "[${COMMITMENT_ID_3}]" -p "${OWNER_ACCOUNT}@active"
assert_commitment_field "${COMMITMENT_ID_3}" "status" "2"

log "Submitting commitment #4 for expire path"
enterprise_use 0 "${COMMIT_EXTREF_4}"
cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" submit \
    "[\"${SUBMITTER_ACCOUNT}\",${SCHEMA_ID},${POLICY_SINGLE_ID},\"${OBJECT_HASH_4}\",\"${COMMIT_EXTREF_4}\"]" \
    -p "${SUBMITTER_ACCOUNT}@active"
COMMITMENT_ID_4="$(get_commitment_id_by_external_ref "${COMMIT_EXTREF_4}")"
cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" expirecmmt "[${COMMITMENT_ID_4}]" -p "${OWNER_ACCOUNT}@active"
assert_commitment_field "${COMMITMENT_ID_4}" "status" "3"

log "Submitting batch #1"
enterprise_use 1 "${BATCH_EXTREF}"
cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" submitroot \
    "[\"${SUBMITTER_ACCOUNT}\",${SCHEMA_ID},${POLICY_BATCH_ID},\"${ROOT_HASH}\",2,\"${BATCH_EXTREF}\"]" \
    -p "${SUBMITTER_ACCOUNT}@active"
BATCH_ID_1="$(get_batch_id_by_external_ref "${BATCH_EXTREF}")"
assert_batch_field "${BATCH_ID_1}" "submitter" "${SUBMITTER_ACCOUNT}"
assert_batch_field "${BATCH_ID_1}" "status" "0"

log "Rejecting duplicate batch request"
if cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" submitroot \
    "[\"${SUBMITTER_ACCOUNT}\",${SCHEMA_ID},${POLICY_BATCH_ID},\"${ROOT_HASH}\",2,\"${BATCH_EXTREF}\"]" \
    -p "${SUBMITTER_ACCOUNT}@active" >/dev/null 2>&1; then
    echo "Assertion failed: duplicate batch request was accepted." >&2
    exit 1
fi

log "Rejecting closebatch before manifest is linked"
if cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" closebatch "[${BATCH_ID_1}]" -p "${SUBMITTER_ACCOUNT}@active" >/dev/null 2>&1; then
    echo "Assertion failed: closebatch succeeded before manifest linking." >&2
    exit 1
fi

log "Linking manifest to batch #1"
cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" linkmanifest "[${BATCH_ID_1},\"${MANIFEST_HASH}\"]" -p "${SUBMITTER_ACCOUNT}@active"
assert_batch_field "${BATCH_ID_1}" "manifest_hash" "${MANIFEST_HASH}"

log "Closing batch #1"
cleos -u "${RPC_URL}" push action "${VERIFICATION_ACCOUNT}" closebatch "[${BATCH_ID_1}]" -p "${SUBMITTER_ACCOUNT}@active"
assert_batch_field "${BATCH_ID_1}" "status" "1"

log "On-chain smoke test passed"
