#!/usr/bin/env bash

set -euo pipefail

RPC_URL="${RPC_URL:-https://jungle4.api.eosnation.io}"
READ_RPC_URL="${READ_RPC_URL:-${RPC_URL}}"
BILLING_ACCOUNT="${BILLING_ACCOUNT:-verifbill}"
VERIFICATION_ACCOUNT="${VERIFICATION_ACCOUNT:-verification}"
OWNER_ACCOUNT="${OWNER_ACCOUNT:-}"
PAYER_ACCOUNT="${PAYER_ACCOUNT:-}"
SUBMITTER_ACCOUNT="${SUBMITTER_ACCOUNT:-}"
PAYMENT_TOKEN_CONTRACT="${PAYMENT_TOKEN_CONTRACT:-eosio.token}"
PAYMENT_SYMBOL="${PAYMENT_SYMBOL:-EOS}"
PAYMENT_PRECISION="${PAYMENT_PRECISION:-4}"
PLAN_CODE="${PLAN_CODE:-smokeplan}"
PACK_CODE="${PACK_CODE:-smokepack}"
PLAN_PRICE="${PLAN_PRICE:-0.0300 EOS}"
PACK_PRICE="${PACK_PRICE:-0.0200 EOS}"
PLAN_DURATION_SEC="${PLAN_DURATION_SEC:-2592000}"
PLAN_INCLUDED_KIB="${PLAN_INCLUDED_KIB:-8}"
PACK_INCLUDED_KIB="${PACK_INCLUDED_KIB:-6}"
USE_SINGLE_BYTES="${USE_SINGLE_BYTES:-1536}"
USE_BATCH_BYTES="${USE_BATCH_BYTES:-3072}"
WAIT_TIMEOUT_SEC="${WAIT_TIMEOUT_SEC:-90}"
WAIT_INTERVAL_SEC="${WAIT_INTERVAL_SEC:-1}"
RUN_EXPIRY_TESTS="${RUN_EXPIRY_TESTS:-false}"
AUTH_TTL_WAIT_SEC="${AUTH_TTL_WAIT_SEC:-610}"

: "${OWNER_ACCOUNT:?Set OWNER_ACCOUNT to the billing contract authority account.}"
: "${PAYER_ACCOUNT:?Set PAYER_ACCOUNT to a funded account that can purchase billing products.}"
: "${SUBMITTER_ACCOUNT:?Set SUBMITTER_ACCOUNT to the account that signs enterprise usage requests.}"

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
PLAN_REF="$(hash_text "bill-plan-${TIMESTAMP}")"
USE_REF_SINGLE="$(hash_text "bill-use-single-${TIMESTAMP}")"
USE_REF_BATCH="$(hash_text "bill-use-batch-${TIMESTAMP}")"
USE_REF_EXPIRED="$(hash_text "bill-use-expired-${TIMESTAMP}")"
USE_REF_TOO_LARGE="$(hash_text "bill-use-too-large-${TIMESTAMP}")"

log "Configuring accepted billing token"
cleos -u "${RPC_URL}" push action "${BILLING_ACCOUNT}" settoken \
    "[\"${PAYMENT_TOKEN_CONTRACT}\",\"${PAYMENT_PRECISION},${PAYMENT_SYMBOL}\"]" \
    -p "${OWNER_ACCOUNT}@active"

log "Configuring verification account for billing consume authorization"
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

EXPECTED_SINGLE_KIB="$(( (USE_SINGLE_BYTES + 1023) / 1024 ))"
EXPECTED_BATCH_KIB="$(( (USE_BATCH_BYTES + 1023) / 1024 ))"

log "Creating enterprise single usage authorization"
cleos -u "${RPC_URL}" push action "${BILLING_ACCOUNT}" use \
    "[\"${PAYER_ACCOUNT}\",\"${SUBMITTER_ACCOUNT}\",0,\"${USE_REF_SINGLE}\",${USE_SINGLE_BYTES}]" \
    -p "${PAYER_ACCOUNT}@active"

wait_for_table_match \
    "${BILLING_ACCOUNT}" \
    "${BILLING_ACCOUNT}" \
    "usageauths" \
    ".rows[] | select(.submitter == \"${SUBMITTER_ACCOUNT}\" and .mode == 0 and ((.consumed == false) or (.consumed == 0)))" \
    "single usage authorization"

log "Rejecting duplicate enterprise single authorization for the same request"
if cleos -u "${RPC_URL}" push action "${BILLING_ACCOUNT}" use \
    "[\"${PAYER_ACCOUNT}\",\"${SUBMITTER_ACCOUNT}\",0,\"${USE_REF_SINGLE}\",${USE_SINGLE_BYTES}]" \
    -p "${PAYER_ACCOUNT}@active" >/dev/null 2>&1; then
    echo "Assertion failed: duplicate enterprise single authorization was accepted." >&2
    exit 1
fi

SINGLE_AUTH_ID="$(get_table_json "${BILLING_ACCOUNT}" "${BILLING_ACCOUNT}" usageauths | "${JQ_BIN}" -r \
    --arg submitter "${SUBMITTER_ACCOUNT}" \
    '.rows[] | select(.submitter == $submitter and .mode == 0 and ((.consumed == false) or (.consumed == 0))) | .auth_id' | tail -n 1)"
SINGLE_ENTITLEMENT_ID="$(get_table_json "${BILLING_ACCOUNT}" "${BILLING_ACCOUNT}" usageauths | "${JQ_BIN}" -r \
    --argjson id "${SINGLE_AUTH_ID}" \
    '.rows[] | select(.auth_id == $id) | .entitlement_id')"
SINGLE_ENTITLEMENT_KIND="$(get_table_json "${BILLING_ACCOUNT}" "${BILLING_ACCOUNT}" entitlements | "${JQ_BIN}" -r \
    --argjson id "${SINGLE_ENTITLEMENT_ID}" \
    '.rows[] | select(.entitlement_id == $id) | .kind')"
SINGLE_ENTITLEMENT_KIB_BEFORE_CONSUME="$(get_table_json "${BILLING_ACCOUNT}" "${BILLING_ACCOUNT}" entitlements | "${JQ_BIN}" -r \
    --argjson id "${SINGLE_ENTITLEMENT_ID}" \
    '.rows[] | select(.entitlement_id == $id) | .kib_remaining')"

SINGLE_AUTH_KIB="$(get_table_json "${BILLING_ACCOUNT}" "${BILLING_ACCOUNT}" usageauths | "${JQ_BIN}" -r \
    --argjson id "${SINGLE_AUTH_ID}" \
    '.rows[] | select(.auth_id == $id) | .billable_kib')"
assert_eq "${EXPECTED_SINGLE_KIB}" "${SINGLE_AUTH_KIB}" "single auth billable_kib"
assert_eq "0" "${SINGLE_ENTITLEMENT_KIND}" "nearest-expiry entitlement kind for single auth"

log "Consuming enterprise single usage authorization"
cleos -u "${RPC_URL}" push action "${BILLING_ACCOUNT}" consume "[${SINGLE_AUTH_ID}]" -p "${OWNER_ACCOUNT}@active"

wait_for_table_match \
    "${BILLING_ACCOUNT}" \
    "${BILLING_ACCOUNT}" \
    "usageauths" \
    ".rows[] | select(.auth_id == ${SINGLE_AUTH_ID} and ((.consumed == true) or (.consumed == 1)))" \
    "consumed single usage authorization"

log "Cleaning consumed enterprise usage authorizations"
cleos -u "${RPC_URL}" push action "${BILLING_ACCOUNT}" cleanauths "[10]" -p "${OWNER_ACCOUNT}@active"

if get_table_json "${BILLING_ACCOUNT}" "${BILLING_ACCOUNT}" usageauths | "${JQ_BIN}" -e \
    --argjson id "${SINGLE_AUTH_ID}" \
    '.rows[] | select(.auth_id == $id)' >/dev/null 2>&1; then
    echo "Assertion failed: consumed single usage authorization was not cleaned up." >&2
    exit 1
fi

PLAN_KIB_AFTER_CONSUME="$(get_table_json "${BILLING_ACCOUNT}" "${BILLING_ACCOUNT}" entitlements | "${JQ_BIN}" -r \
    --argjson id "${SINGLE_ENTITLEMENT_ID}" \
    '.rows[] | select(.entitlement_id == $id) | .kib_remaining')"
assert_eq "$(( SINGLE_ENTITLEMENT_KIB_BEFORE_CONSUME - EXPECTED_SINGLE_KIB ))" "${PLAN_KIB_AFTER_CONSUME}" "selected entitlement kib_remaining after single consume"

log "Reissuing enterprise authorization for the same request after cleanup"
LAST_AUTH_ID_BEFORE_REISSUE="$(get_table_json "${BILLING_ACCOUNT}" "${BILLING_ACCOUNT}" usageauths | "${JQ_BIN}" -r '[.rows[].auth_id] | max // 0')"
cleos -u "${RPC_URL}" push action "${BILLING_ACCOUNT}" use \
    "[\"${PAYER_ACCOUNT}\",\"${SUBMITTER_ACCOUNT}\",0,\"${USE_REF_SINGLE}\",${USE_SINGLE_BYTES}]" \
    -p "${PAYER_ACCOUNT}@active"

REISSUED_AUTH_ID="$(get_table_json "${BILLING_ACCOUNT}" "${BILLING_ACCOUNT}" usageauths | "${JQ_BIN}" -r \
    --arg submitter "${SUBMITTER_ACCOUNT}" \
    --argjson last_id "${LAST_AUTH_ID_BEFORE_REISSUE}" \
    '.rows[] | select(.submitter == $submitter and .mode == 0 and .auth_id > $last_id and ((.consumed == false) or (.consumed == 0))) | .auth_id' | tail -n 1)"

if [[ -z "${REISSUED_AUTH_ID}" || "${REISSUED_AUTH_ID}" == "${SINGLE_AUTH_ID}" ]]; then
    echo "Assertion failed: enterprise authorization was not reissued after cleanup." >&2
    exit 1
fi

log "Consuming reissued enterprise authorization"
cleos -u "${RPC_URL}" push action "${BILLING_ACCOUNT}" consume "[${REISSUED_AUTH_ID}]" -p "${OWNER_ACCOUNT}@active"
cleos -u "${RPC_URL}" push action "${BILLING_ACCOUNT}" cleanauths "[10]" -p "${OWNER_ACCOUNT}@active"

TOO_LARGE_BYTES="$(( (PLAN_INCLUDED_KIB + 2) * 1024 ))"
log "Rejecting enterprise authorization larger than any single entitlement"
if cleos -u "${RPC_URL}" push action "${BILLING_ACCOUNT}" use \
    "[\"${PAYER_ACCOUNT}\",\"${SUBMITTER_ACCOUNT}\",0,\"${USE_REF_TOO_LARGE}\",${TOO_LARGE_BYTES}]" \
    -p "${PAYER_ACCOUNT}@active" >/dev/null 2>&1; then
    echo "Assertion failed: oversized enterprise authorization was accepted." >&2
    exit 1
fi

log "Creating enterprise batch usage authorization"
cleos -u "${RPC_URL}" push action "${BILLING_ACCOUNT}" use \
    "[\"${PAYER_ACCOUNT}\",\"${SUBMITTER_ACCOUNT}\",1,\"${USE_REF_BATCH}\",${USE_BATCH_BYTES}]" \
    -p "${PAYER_ACCOUNT}@active"

wait_for_table_match \
    "${BILLING_ACCOUNT}" \
    "${BILLING_ACCOUNT}" \
    "usageauths" \
    ".rows[] | select(.submitter == \"${SUBMITTER_ACCOUNT}\" and .mode == 1 and ((.consumed == false) or (.consumed == 0)))" \
    "batch usage authorization"

BATCH_AUTH_ID="$(get_table_json "${BILLING_ACCOUNT}" "${BILLING_ACCOUNT}" usageauths | "${JQ_BIN}" -r \
    --arg submitter "${SUBMITTER_ACCOUNT}" \
    '.rows[] | select(.submitter == $submitter and .mode == 1 and ((.consumed == false) or (.consumed == 0))) | .auth_id' | tail -n 1)"

BATCH_AUTH_KIB="$(get_table_json "${BILLING_ACCOUNT}" "${BILLING_ACCOUNT}" usageauths | "${JQ_BIN}" -r \
    --argjson id "${BATCH_AUTH_ID}" \
    '.rows[] | select(.auth_id == $id) | .billable_kib')"
assert_eq "${EXPECTED_BATCH_KIB}" "${BATCH_AUTH_KIB}" "batch auth billable_kib"

if [[ "${RUN_EXPIRY_TESTS}" == "true" ]]; then
    log "Creating enterprise auth for expiry/reissue test"
    cleos -u "${RPC_URL}" push action "${BILLING_ACCOUNT}" use \
        "[\"${PAYER_ACCOUNT}\",\"${SUBMITTER_ACCOUNT}\",0,\"${USE_REF_EXPIRED}\",${USE_SINGLE_BYTES}]" \
        -p "${PAYER_ACCOUNT}@active"

    EXPIRED_AUTH_ID="$(get_table_json "${BILLING_ACCOUNT}" "${BILLING_ACCOUNT}" usageauths | "${JQ_BIN}" -r \
        --arg submitter "${SUBMITTER_ACCOUNT}" \
        '.rows[] | select(.submitter == $submitter and .mode == 0 and ((.consumed == false) or (.consumed == 0))) | .auth_id' | tail -n 1)"

    log "Waiting ${AUTH_TTL_WAIT_SEC}s for enterprise auth to expire"
    sleep "${AUTH_TTL_WAIT_SEC}"

    log "Cleaning expired enterprise authorizations"
    cleos -u "${RPC_URL}" push action "${BILLING_ACCOUNT}" cleanauths "[10]" -p "${OWNER_ACCOUNT}@active"

    if get_table_json "${BILLING_ACCOUNT}" "${BILLING_ACCOUNT}" usageauths | "${JQ_BIN}" -e \
        --argjson id "${EXPIRED_AUTH_ID}" \
        '.rows[] | select(.auth_id == $id)' >/dev/null 2>&1; then
        echo "Assertion failed: expired enterprise authorization was not cleaned up." >&2
        exit 1
    fi

    log "Reissuing enterprise auth after expiry cleanup"
    LAST_AUTH_ID_BEFORE_EXPIRY_REISSUE="$(get_table_json "${BILLING_ACCOUNT}" "${BILLING_ACCOUNT}" usageauths | "${JQ_BIN}" -r '[.rows[].auth_id] | max // 0')"
    cleos -u "${RPC_URL}" push action "${BILLING_ACCOUNT}" use \
        "[\"${PAYER_ACCOUNT}\",\"${SUBMITTER_ACCOUNT}\",0,\"${USE_REF_EXPIRED}\",${USE_SINGLE_BYTES}]" \
        -p "${PAYER_ACCOUNT}@active"

    REISSUED_EXPIRED_AUTH_ID="$(get_table_json "${BILLING_ACCOUNT}" "${BILLING_ACCOUNT}" usageauths | "${JQ_BIN}" -r \
        --arg submitter "${SUBMITTER_ACCOUNT}" \
        --argjson last_id "${LAST_AUTH_ID_BEFORE_EXPIRY_REISSUE}" \
        '.rows[] | select(.submitter == $submitter and .mode == 0 and .auth_id > $last_id and ((.consumed == false) or (.consumed == 0))) | .auth_id' | tail -n 1)"

    if [[ -z "${REISSUED_EXPIRED_AUTH_ID}" || "${REISSUED_EXPIRED_AUTH_ID}" == "${EXPIRED_AUTH_ID}" ]]; then
        echo "Assertion failed: enterprise auth was not reissued after expiry cleanup." >&2
        exit 1
    fi
fi

log "Enterprise billing smoke test passed"
