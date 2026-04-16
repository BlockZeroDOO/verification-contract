#!/usr/bin/env bash

set -euo pipefail

RPC_URL="${RPC_URL:-https://jungle4.api.eosnation.io}"
READ_RPC_URL="${READ_RPC_URL:-${RPC_URL}}"
RETPAY_ACCOUNT="${RETPAY_ACCOUNT:-verifretpay}"
OWNER_ACCOUNT="${OWNER_ACCOUNT:-}"
SUBMITTER_ACCOUNT="${SUBMITTER_ACCOUNT:-}"
PAYMENT_TOKEN_CONTRACT="${PAYMENT_TOKEN_CONTRACT:-eosio.token}"
PAYMENT_SYMBOL="${PAYMENT_SYMBOL:-EOS}"
PAYMENT_PRECISION="${PAYMENT_PRECISION:-4}"
PRICE_SINGLE="${PRICE_SINGLE:-0.0100 EOS}"
PRICE_BATCH="${PRICE_BATCH:-0.0200 EOS}"
UNDERPAY_SINGLE="${UNDERPAY_SINGLE:-0.0090 EOS}"
WRONG_TOKEN_CONTRACT="${WRONG_TOKEN_CONTRACT:-retail.fake}"
WAIT_TIMEOUT_SEC="${WAIT_TIMEOUT_SEC:-90}"
WAIT_INTERVAL_SEC="${WAIT_INTERVAL_SEC:-1}"

: "${OWNER_ACCOUNT:?Set OWNER_ACCOUNT to the retail payment contract authority account.}"
: "${SUBMITTER_ACCOUNT:?Set SUBMITTER_ACCOUNT to a funded test account that can sign transfers.}"

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

get_table_json() {
    local code="$1"
    local scope="$2"
    local table="$3"
    cleos -u "${READ_RPC_URL}" get table "${code}" "${scope}" "${table}" --limit 1000
}

wait_for_auth_request() {
    local submitter="$1"
    local external_ref="$2"
    local description="$3"

    local deadline=$(( $(date -u +%s) + WAIT_TIMEOUT_SEC ))
    while true; do
        if get_table_json "${RETPAY_ACCOUNT}" "${RETPAY_ACCOUNT}" "rtlauths" | \
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

wait_for_consumed_auth() {
    local auth_id="$1"
    local description="$2"

    local deadline=$(( $(date -u +%s) + WAIT_TIMEOUT_SEC ))
    while true; do
        if get_table_json "${RETPAY_ACCOUNT}" "${RETPAY_ACCOUNT}" "rtlauths" | \
            "${JQ_BIN}" -e ".rows[] | select(.auth_id == ${auth_id} and .consumed == true)" >/dev/null 2>&1; then
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
EXTREF_SINGLE="$(hash_text "retpay-single-${TIMESTAMP}")"
EXTREF_BATCH="$(hash_text "retpay-batch-${TIMESTAMP}")"

log "Configuring accepted retail payment token"
cleos -u "${RPC_URL}" push action "${RETPAY_ACCOUNT}" settoken \
    "[\"${PAYMENT_TOKEN_CONTRACT}\",\"${PAYMENT_PRECISION},${PAYMENT_SYMBOL}\"]" \
    -p "${OWNER_ACCOUNT}@active"

log "Configuring retail single tariff"
cleos -u "${RPC_URL}" push action "${RETPAY_ACCOUNT}" setprice \
    "[0,\"${PAYMENT_TOKEN_CONTRACT}\",\"${PRICE_SINGLE}\"]" \
    -p "${OWNER_ACCOUNT}@active"

log "Configuring retail batch tariff"
cleos -u "${RPC_URL}" push action "${RETPAY_ACCOUNT}" setprice \
    "[1,\"${PAYMENT_TOKEN_CONTRACT}\",\"${PRICE_BATCH}\"]" \
    -p "${OWNER_ACCOUNT}@active"

log "Rejecting underpayment for retail single authorization"
if cleos -u "${RPC_URL}" transfer "${SUBMITTER_ACCOUNT}" "${RETPAY_ACCOUNT}" "${UNDERPAY_SINGLE}" \
    "single|${SUBMITTER_ACCOUNT}|${EXTREF_SINGLE}" >/dev/null 2>&1; then
    echo "Assertion failed: underpayment retail authorization transfer was accepted." >&2
    exit 1
fi

log "Rejecting wrong token for retail single authorization"
if cleos -u "${RPC_URL}" push action "${WRONG_TOKEN_CONTRACT}" transfer \
    "[\"${SUBMITTER_ACCOUNT}\",\"${RETPAY_ACCOUNT}\",\"${PRICE_SINGLE}\",\"single|${SUBMITTER_ACCOUNT}|${EXTREF_SINGLE}\"]" \
    -p "${SUBMITTER_ACCOUNT}@active" >/dev/null 2>&1; then
    echo "Assertion failed: wrong-token retail authorization was accepted." >&2
    exit 1
fi

log "Funding exact retail single authorization"
cleos -u "${RPC_URL}" transfer "${SUBMITTER_ACCOUNT}" "${RETPAY_ACCOUNT}" "${PRICE_SINGLE}" \
    "single|${SUBMITTER_ACCOUNT}|${EXTREF_SINGLE}"

wait_for_auth_request "${SUBMITTER_ACCOUNT}" "${EXTREF_SINGLE}" "retail single authorization"

log "Rejecting duplicate retail single authorization for the same request"
if cleos -u "${RPC_URL}" transfer "${SUBMITTER_ACCOUNT}" "${RETPAY_ACCOUNT}" "${PRICE_SINGLE}" \
    "single|${SUBMITTER_ACCOUNT}|${EXTREF_SINGLE}" >/dev/null 2>&1; then
    echo "Assertion failed: duplicate retail authorization was accepted for the same request." >&2
    exit 1
fi

SINGLE_AUTH_ID="$(get_table_json "${RETPAY_ACCOUNT}" "${RETPAY_ACCOUNT}" rtlauths | "${JQ_BIN}" -r \
    --arg submitter "${SUBMITTER_ACCOUNT}" \
    --arg external_ref "${EXTREF_SINGLE}" \
    '.rows[] | select(.submitter == $submitter and .external_ref == $external_ref and .consumed == false) | .auth_id' | tail -n 1)"

log "Consuming retail single authorization"
cleos -u "${RPC_URL}" push action "${RETPAY_ACCOUNT}" consume "[${SINGLE_AUTH_ID}]" -p "${OWNER_ACCOUNT}@active"

wait_for_consumed_auth "${SINGLE_AUTH_ID}" "consumed retail single authorization"

log "Funding exact retail batch authorization"
cleos -u "${RPC_URL}" transfer "${SUBMITTER_ACCOUNT}" "${RETPAY_ACCOUNT}" "${PRICE_BATCH}" \
    "batch|${SUBMITTER_ACCOUNT}|${EXTREF_BATCH}"

wait_for_auth_request "${SUBMITTER_ACCOUNT}" "${EXTREF_BATCH}" "retail batch authorization"

log "Retail payment authorization smoke test passed"
