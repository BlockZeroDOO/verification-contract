#!/usr/bin/env bash

set -euo pipefail

RPC_URL="${RPC_URL:-https://jungle4.api.eosnation.io}"
READ_RPC_URL="${READ_RPC_URL:-${RPC_URL}}"
RETPAY_ACCOUNT="${RETPAY_ACCOUNT:-verifretpay}"
VERIFICATION_ACCOUNT="${VERIFICATION_ACCOUNT:-verification}"
OWNER_ACCOUNT="${OWNER_ACCOUNT:-}"
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
RUN_EXPIRY_TESTS="${RUN_EXPIRY_TESTS:-false}"
AUTH_TTL_WAIT_SEC="${AUTH_TTL_WAIT_SEC:-610}"

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
            "${JQ_BIN}" -e ".rows[] | select(.auth_id == ${auth_id} and ((.consumed == true) or (.consumed == 1)))" >/dev/null 2>&1; then
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
EXTREF_EXPIRED="$(hash_text "retpay-expired-${TIMESTAMP}")"
SINGLE_KIB="$(( (BILLABLE_BYTES_SINGLE + 1023) / 1024 ))"
BATCH_KIB="$(( (BILLABLE_BYTES_BATCH + 1023) / 1024 ))"
SINGLE_TOTAL_UNITS="$(( SINGLE_KIB * $(asset_to_units "${PRICE_PER_KIB_SINGLE}") ))"
BATCH_TOTAL_UNITS="$(( BATCH_KIB * $(asset_to_units "${PRICE_PER_KIB_BATCH}") ))"
PRICE_SINGLE="$(units_to_asset "${SINGLE_TOTAL_UNITS}" "${PAYMENT_SYMBOL}")"
PRICE_BATCH="$(units_to_asset "${BATCH_TOTAL_UNITS}" "${PAYMENT_SYMBOL}")"
UNDERPAY_SINGLE="$(units_to_asset "$(( SINGLE_TOTAL_UNITS - 1 ))" "${PAYMENT_SYMBOL}")"

log "Configuring accepted retail payment token"
cleos -u "${RPC_URL}" push action "${RETPAY_ACCOUNT}" settoken \
    "[\"${PAYMENT_TOKEN_CONTRACT}\",\"${PAYMENT_PRECISION},${PAYMENT_SYMBOL}\"]" \
    -p "${OWNER_ACCOUNT}@active"

log "Configuring verification account for retail payment consume authorization"
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

log "Rejecting underpayment for retail single authorization"
if cleos -u "${RPC_URL}" transfer "${SUBMITTER_ACCOUNT}" "${RETPAY_ACCOUNT}" "${UNDERPAY_SINGLE}" \
    "single|${SUBMITTER_ACCOUNT}|${EXTREF_SINGLE}|${BILLABLE_BYTES_SINGLE}" >/dev/null 2>&1; then
    echo "Assertion failed: underpayment retail authorization transfer was accepted." >&2
    exit 1
fi

log "Rejecting wrong token for retail single authorization"
if cleos -u "${RPC_URL}" push action "${WRONG_TOKEN_CONTRACT}" transfer \
    "[\"${SUBMITTER_ACCOUNT}\",\"${RETPAY_ACCOUNT}\",\"${PRICE_SINGLE}\",\"single|${SUBMITTER_ACCOUNT}|${EXTREF_SINGLE}|${BILLABLE_BYTES_SINGLE}\"]" \
    -p "${SUBMITTER_ACCOUNT}@active" >/dev/null 2>&1; then
    echo "Assertion failed: wrong-token retail authorization was accepted." >&2
    exit 1
fi

log "Funding exact retail single authorization"
cleos -u "${RPC_URL}" transfer "${SUBMITTER_ACCOUNT}" "${RETPAY_ACCOUNT}" "${PRICE_SINGLE}" \
    "single|${SUBMITTER_ACCOUNT}|${EXTREF_SINGLE}|${BILLABLE_BYTES_SINGLE}"

wait_for_auth_request "${SUBMITTER_ACCOUNT}" "${EXTREF_SINGLE}" "retail single authorization"

log "Rejecting duplicate retail single authorization for the same request"
if cleos -u "${RPC_URL}" transfer "${SUBMITTER_ACCOUNT}" "${RETPAY_ACCOUNT}" "${PRICE_SINGLE}" \
    "single|${SUBMITTER_ACCOUNT}|${EXTREF_SINGLE}|${BILLABLE_BYTES_SINGLE}" >/dev/null 2>&1; then
    echo "Assertion failed: duplicate retail authorization was accepted for the same request." >&2
    exit 1
fi

SINGLE_AUTH_ID="$(get_table_json "${RETPAY_ACCOUNT}" "${RETPAY_ACCOUNT}" rtlauths | "${JQ_BIN}" -r \
    --arg submitter "${SUBMITTER_ACCOUNT}" \
    --arg external_ref "${EXTREF_SINGLE}" \
    '.rows[] | select(.submitter == $submitter and .external_ref == $external_ref and ((.consumed == false) or (.consumed == 0))) | .auth_id' | tail -n 1)"

SINGLE_AUTH_KIB="$(get_table_json "${RETPAY_ACCOUNT}" "${RETPAY_ACCOUNT}" rtlauths | "${JQ_BIN}" -r \
    --argjson id "${SINGLE_AUTH_ID}" \
    '.rows[] | select(.auth_id == $id) | .billable_kib')"
if [[ "${SINGLE_AUTH_KIB}" != "${SINGLE_KIB}" ]]; then
    echo "Assertion failed: retail single auth billable_kib mismatch." >&2
    exit 1
fi

log "Consuming retail single authorization"
cleos -u "${RPC_URL}" push action "${RETPAY_ACCOUNT}" consume "[${SINGLE_AUTH_ID}]" -p "${OWNER_ACCOUNT}@active"

wait_for_consumed_auth "${SINGLE_AUTH_ID}" "consumed retail single authorization"

log "Cleaning consumed retail authorization"
cleos -u "${RPC_URL}" push action "${RETPAY_ACCOUNT}" cleanauths "[10]" -p "${OWNER_ACCOUNT}@active"

if get_table_json "${RETPAY_ACCOUNT}" "${RETPAY_ACCOUNT}" rtlauths | "${JQ_BIN}" -e \
    --argjson id "${SINGLE_AUTH_ID}" \
    '.rows[] | select(.auth_id == $id)' >/dev/null 2>&1; then
    echo "Assertion failed: consumed retail authorization was not cleaned up." >&2
    exit 1
fi

log "Reissuing retail single authorization for the same request after cleanup"
cleos -u "${RPC_URL}" transfer "${SUBMITTER_ACCOUNT}" "${RETPAY_ACCOUNT}" "${PRICE_SINGLE}" \
    "single|${SUBMITTER_ACCOUNT}|${EXTREF_SINGLE}|${BILLABLE_BYTES_SINGLE}"

wait_for_auth_request "${SUBMITTER_ACCOUNT}" "${EXTREF_SINGLE}" "reissued retail single authorization"

REISSUED_SINGLE_AUTH_ID="$(get_table_json "${RETPAY_ACCOUNT}" "${RETPAY_ACCOUNT}" rtlauths | "${JQ_BIN}" -r \
    --arg submitter "${SUBMITTER_ACCOUNT}" \
    --arg external_ref "${EXTREF_SINGLE}" \
    '.rows[] | select(.submitter == $submitter and .external_ref == $external_ref and ((.consumed == false) or (.consumed == 0))) | .auth_id' | tail -n 1)"

if [[ -z "${REISSUED_SINGLE_AUTH_ID}" || "${REISSUED_SINGLE_AUTH_ID}" == "${SINGLE_AUTH_ID}" ]]; then
    echo "Assertion failed: retail authorization was not reissued after cleanup." >&2
    exit 1
fi

log "Consuming reissued retail authorization"
cleos -u "${RPC_URL}" push action "${RETPAY_ACCOUNT}" consume "[${REISSUED_SINGLE_AUTH_ID}]" -p "${OWNER_ACCOUNT}@active"
cleos -u "${RPC_URL}" push action "${RETPAY_ACCOUNT}" cleanauths "[10]" -p "${OWNER_ACCOUNT}@active"

log "Funding exact retail batch authorization"
cleos -u "${RPC_URL}" transfer "${SUBMITTER_ACCOUNT}" "${RETPAY_ACCOUNT}" "${PRICE_BATCH}" \
    "batch|${SUBMITTER_ACCOUNT}|${EXTREF_BATCH}|${BILLABLE_BYTES_BATCH}"

wait_for_auth_request "${SUBMITTER_ACCOUNT}" "${EXTREF_BATCH}" "retail batch authorization"

BATCH_AUTH_ID="$(get_table_json "${RETPAY_ACCOUNT}" "${RETPAY_ACCOUNT}" rtlauths | "${JQ_BIN}" -r \
    --arg submitter "${SUBMITTER_ACCOUNT}" \
    --arg external_ref "${EXTREF_BATCH}" \
    '.rows[] | select(.submitter == $submitter and .external_ref == $external_ref and ((.consumed == false) or (.consumed == 0))) | .auth_id' | tail -n 1)"

BATCH_AUTH_KIB="$(get_table_json "${RETPAY_ACCOUNT}" "${RETPAY_ACCOUNT}" rtlauths | "${JQ_BIN}" -r \
    --argjson id "${BATCH_AUTH_ID}" \
    '.rows[] | select(.auth_id == $id) | .billable_kib')"
if [[ "${BATCH_AUTH_KIB}" != "${BATCH_KIB}" ]]; then
    echo "Assertion failed: retail batch auth billable_kib mismatch." >&2
    exit 1
fi

if [[ "${RUN_EXPIRY_TESTS}" == "true" ]]; then
    log "Funding retail authorization for expiry/reissue test"
    cleos -u "${RPC_URL}" transfer "${SUBMITTER_ACCOUNT}" "${RETPAY_ACCOUNT}" "${PRICE_SINGLE}" \
        "single|${SUBMITTER_ACCOUNT}|${EXTREF_EXPIRED}|${BILLABLE_BYTES_SINGLE}"

    wait_for_auth_request "${SUBMITTER_ACCOUNT}" "${EXTREF_EXPIRED}" "retail authorization for expiry test"

    log "Waiting ${AUTH_TTL_WAIT_SEC}s for retail auth to expire"
    sleep "${AUTH_TTL_WAIT_SEC}"

    log "Cleaning expired retail authorizations"
    cleos -u "${RPC_URL}" push action "${RETPAY_ACCOUNT}" cleanauths "[10]" -p "${OWNER_ACCOUNT}@active"

    if get_table_json "${RETPAY_ACCOUNT}" "${RETPAY_ACCOUNT}" rtlauths | "${JQ_BIN}" -e \
        --arg submitter "${SUBMITTER_ACCOUNT}" \
        --arg external_ref "${EXTREF_EXPIRED}" \
        '.rows[] | select(.submitter == $submitter and .external_ref == $external_ref)' >/dev/null 2>&1; then
        echo "Assertion failed: expired retail authorization was not cleaned up." >&2
        exit 1
    fi

    log "Reissuing retail auth after expiry cleanup"
    cleos -u "${RPC_URL}" transfer "${SUBMITTER_ACCOUNT}" "${RETPAY_ACCOUNT}" "${PRICE_SINGLE}" \
        "single|${SUBMITTER_ACCOUNT}|${EXTREF_EXPIRED}|${BILLABLE_BYTES_SINGLE}"
fi

log "Retail payment authorization smoke test passed"
