#!/usr/bin/env bash

set -euo pipefail

RPC_URL="${RPC_URL:-https://jungle4.api.eosnation.io}"
READ_RPC_URL="${READ_RPC_URL:-${RPC_URL}}"
RETAIL_ACCOUNT="${RETAIL_ACCOUNT:-verifretail}"
OWNER_ACCOUNT="${OWNER_ACCOUNT:-}"
SUBMITTER_ACCOUNT="${SUBMITTER_ACCOUNT:-}"
PAYMENT_TOKEN_CONTRACT="${PAYMENT_TOKEN_CONTRACT:-eosio.token}"
PAYMENT_SYMBOL="${PAYMENT_SYMBOL:-EOS}"
WAIT_TIMEOUT_SEC="${WAIT_TIMEOUT_SEC:-90}"
WAIT_INTERVAL_SEC="${WAIT_INTERVAL_SEC:-1}"

: "${OWNER_ACCOUNT:?Set OWNER_ACCOUNT to the retail contract authority account.}"
: "${SUBMITTER_ACCOUNT:?Set SUBMITTER_ACCOUNT to a funded test account that can sign submits and transfers.}"

if [[ ${#RETAIL_ACCOUNT} -gt 12 ]]; then
    echo "RETAIL_ACCOUNT must be 12 characters or fewer for Antelope account names: ${RETAIL_ACCOUNT}" >&2
    exit 1
fi

if ! command -v cleos >/dev/null 2>&1; then
    echo "cleos is required for smoke-test-retail.sh" >&2
    exit 1
fi

if command -v jq >/dev/null 2>&1; then
    JQ_BIN="jq"
else
    echo "jq is required for smoke-test-retail.sh" >&2
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
    printf '[smoke-test-retail] %s\n' "$1"
}

log "WARNING: verifretail is a deprecated compatibility path."
log "WARNING: Prefer unified retail validation with verif + verifretpay for new deployments."

get_table_json() {
    local code="$1"
    local scope="$2"
    local table="$3"
    cleos -u "${READ_RPC_URL}" get table "${code}" "${scope}" "${table}"
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

wait_for_receipt_state() {
    local submitter="$1"
    local external_ref="$2"
    local description="$3"

    local deadline=$(( $(date -u +%s) + WAIT_TIMEOUT_SEC ))
    while true; do
        if get_table_json "${RETAIL_ACCOUNT}" "${RETAIL_ACCOUNT}" "rtlreceipts" | \
            "${JQ_BIN}" -r '.rows[] | "\(.submitter)\t\(.external_ref)"' | \
            grep -Fx -- "$(printf '%s\t%s' "${submitter}" "${external_ref}")" >/dev/null 2>&1; then
            return 0
        fi

        if (( $(date -u +%s) >= deadline )); then
            echo "Timed out waiting for ${description}." >&2
            exit 1
        fi

        sleep "${WAIT_INTERVAL_SEC}"
    done
}

wait_for_commitment_request() {
    local submitter="$1"
    local external_ref="$2"
    local description="$3"

    local deadline=$(( $(date -u +%s) + WAIT_TIMEOUT_SEC ))
    while true; do
        if get_table_json "${RETAIL_ACCOUNT}" "${RETAIL_ACCOUNT}" "commitments" | \
            "${JQ_BIN}" -r '.rows[] | "\(.submitter)\t\(.external_ref)"' | \
            grep -Fx -- "$(printf '%s\t%s' "${submitter}" "${external_ref}")" >/dev/null 2>&1; then
            return 0
        fi

        if (( $(date -u +%s) >= deadline )); then
            echo "Timed out waiting for ${description}." >&2
            exit 1
        fi

        sleep "${WAIT_INTERVAL_SEC}"
    done
}

wait_for_batch_request() {
    local submitter="$1"
    local external_ref="$2"
    local description="$3"

    local deadline=$(( $(date -u +%s) + WAIT_TIMEOUT_SEC ))
    while true; do
        if get_table_json "${RETAIL_ACCOUNT}" "${RETAIL_ACCOUNT}" "batches" | \
            "${JQ_BIN}" -r '.rows[] | "\(.submitter)\t\(.external_ref)"' | \
            grep -Fx -- "$(printf '%s\t%s' "${submitter}" "${external_ref}")" >/dev/null 2>&1; then
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

SCHEMA_ID="${SCHEMA_ID:-$((BASE_ID + 3000))}"
POLICY_SINGLE_ID="${POLICY_SINGLE_ID:-$((BASE_ID + 4000))}"
POLICY_BATCH_ID="${POLICY_BATCH_ID:-$((BASE_ID + 4001))}"

PRICE_SINGLE="${PRICE_SINGLE:-0.0100 ${PAYMENT_SYMBOL}}"
PRICE_BATCH="${PRICE_BATCH:-0.0200 ${PAYMENT_SYMBOL}}"
UNDERPAY_SINGLE="${UNDERPAY_SINGLE:-0.0090 ${PAYMENT_SYMBOL}}"
WRONG_TOKEN_CONTRACT="${WRONG_TOKEN_CONTRACT:-retail.fake}"

EXTREF_SINGLE="$(hash_text "rtl-single-${TIMESTAMP}")"
EXTREF_BATCH="$(hash_text "rtl-batch-${TIMESTAMP}")"
OBJECT_HASH="$(hash_text "rtl-object-${TIMESTAMP}")"
ROOT_HASH="$(hash_text "rtl-root-${TIMESTAMP}")"

log "Configuring accepted payment token"
cleos -u "${RPC_URL}" push action "${RETAIL_ACCOUNT}" settoken \
    "[\"${PAYMENT_TOKEN_CONTRACT}\",\"4,${PAYMENT_SYMBOL}\"]" \
    -p "${OWNER_ACCOUNT}@active"

log "Configuring retail single tariff"
cleos -u "${RPC_URL}" push action "${RETAIL_ACCOUNT}" setprice \
    "[0,\"${PAYMENT_TOKEN_CONTRACT}\",\"${PRICE_SINGLE}\"]" \
    -p "${OWNER_ACCOUNT}@active"

log "Configuring retail batch tariff"
cleos -u "${RPC_URL}" push action "${RETAIL_ACCOUNT}" setprice \
    "[1,\"${PAYMENT_TOKEN_CONTRACT}\",\"${PRICE_BATCH}\"]" \
    -p "${OWNER_ACCOUNT}@active"

log "Creating retail schema"
cleos -u "${RPC_URL}" push action "${RETAIL_ACCOUNT}" addschema \
    "[${SCHEMA_ID},\"1.0.0\",\"$(hash_text "rtl-schema-${TIMESTAMP}")\",\"$(hash_text "rtl-policy-${TIMESTAMP}")\"]" \
    -p "${OWNER_ACCOUNT}@active"

log "Creating retail single policy"
cleos -u "${RPC_URL}" push action "${RETAIL_ACCOUNT}" setpolicy \
    "[${POLICY_SINGLE_ID},true,false,false,0,true]" \
    -p "${OWNER_ACCOUNT}@active"

log "Creating retail batch policy"
cleos -u "${RPC_URL}" push action "${RETAIL_ACCOUNT}" setpolicy \
    "[${POLICY_BATCH_ID},false,true,false,0,true]" \
    -p "${OWNER_ACCOUNT}@active"

log "Rejecting underpayment for single flow"
if cleos -u "${RPC_URL}" transfer "${SUBMITTER_ACCOUNT}" "${RETAIL_ACCOUNT}" "${UNDERPAY_SINGLE}" \
    "single|${SUBMITTER_ACCOUNT}|${EXTREF_SINGLE}" >/dev/null 2>&1; then
    echo "Assertion failed: underpayment transfer was accepted." >&2
    exit 1
fi

log "Rejecting wrong token for single flow"
if cleos -u "${RPC_URL}" push action "${WRONG_TOKEN_CONTRACT}" transfer \
    "[\"${SUBMITTER_ACCOUNT}\",\"${RETAIL_ACCOUNT}\",\"${PRICE_SINGLE}\",\"single|${SUBMITTER_ACCOUNT}|${EXTREF_SINGLE}\"]" \
    -p "${SUBMITTER_ACCOUNT}@active" >/dev/null 2>&1; then
    echo "Assertion failed: wrong-token retail payment was accepted." >&2
    exit 1
fi

log "Funding exact retail single payment"
cleos -u "${RPC_URL}" transfer "${SUBMITTER_ACCOUNT}" "${RETAIL_ACCOUNT}" "${PRICE_SINGLE}" \
    "single|${SUBMITTER_ACCOUNT}|${EXTREF_SINGLE}"

wait_for_receipt_state "${SUBMITTER_ACCOUNT}" "${EXTREF_SINGLE}" "retail single receipt"

log "Submitting retail single commitment"
cleos -u "${RPC_URL}" push action "${RETAIL_ACCOUNT}" submit \
    "[\"${SUBMITTER_ACCOUNT}\",${SCHEMA_ID},${POLICY_SINGLE_ID},\"${OBJECT_HASH}\",\"${EXTREF_SINGLE}\"]" \
    -p "${SUBMITTER_ACCOUNT}@active"

wait_for_commitment_request "${SUBMITTER_ACCOUNT}" "${EXTREF_SINGLE}" "retail single commitment"

log "Rejecting duplicate retail single submit without a new payment"
if cleos -u "${RPC_URL}" push action "${RETAIL_ACCOUNT}" submit \
    "[\"${SUBMITTER_ACCOUNT}\",${SCHEMA_ID},${POLICY_SINGLE_ID},\"${OBJECT_HASH}\",\"${EXTREF_SINGLE}\"]" \
    -p "${SUBMITTER_ACCOUNT}@active" >/dev/null 2>&1; then
    echo "Assertion failed: duplicate retail single submit was accepted without new payment." >&2
    exit 1
fi

log "Funding exact retail batch payment"
cleos -u "${RPC_URL}" transfer "${SUBMITTER_ACCOUNT}" "${RETAIL_ACCOUNT}" "${PRICE_BATCH}" \
    "batch|${SUBMITTER_ACCOUNT}|${EXTREF_BATCH}"

wait_for_receipt_state "${SUBMITTER_ACCOUNT}" "${EXTREF_BATCH}" "retail batch receipt"

log "Submitting retail batch root"
cleos -u "${RPC_URL}" push action "${RETAIL_ACCOUNT}" submitroot \
    "[\"${SUBMITTER_ACCOUNT}\",${SCHEMA_ID},${POLICY_BATCH_ID},\"${ROOT_HASH}\",2,\"${EXTREF_BATCH}\"]" \
    -p "${SUBMITTER_ACCOUNT}@active"

wait_for_batch_request "${SUBMITTER_ACCOUNT}" "${EXTREF_BATCH}" "retail batch record"

log "Retail atomic pay + submit smoke test passed"
