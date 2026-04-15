#!/usr/bin/env bash

set -euo pipefail

RPC_URL="${RPC_URL:-https://history.denotary.io}"
DFS_ACCOUNT="${DFS_ACCOUNT:-dfs}"
PAYMENT_TOKEN_CONTRACT="${PAYMENT_TOKEN_CONTRACT:-eosio.token}"
PAYMENT_AMOUNT="${PAYMENT_AMOUNT:-5.0000 EOS}"
WAIT_TIMEOUT_SEC="${WAIT_TIMEOUT_SEC:-30}"
WAIT_INTERVAL_SEC="${WAIT_INTERVAL_SEC:-1}"

: "${DFS_SETTLEMENT_ACCOUNT:?Set DFS_SETTLEMENT_ACCOUNT to the configured settlement_authority account.}"
: "${DFS_PAYER_ACCOUNT:?Set DFS_PAYER_ACCOUNT to the payer account for the test transfer.}"

if ! command -v cleos >/dev/null 2>&1; then
    echo "cleos is required for smoke-test-dfs.sh" >&2
    exit 1
fi

if ! command -v jq >/dev/null 2>&1; then
    echo "jq is required for smoke-test-dfs.sh" >&2
    exit 1
fi

log() {
    printf '[smoke-test-dfs] %s\n' "$1"
}

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

get_table_json() {
    local code="$1"
    local scope="$2"
    local table="$3"
    cleos -u "${RPC_URL}" get table "${code}" "${scope}" "${table}"
}

wait_for_table_match() {
    local code="$1"
    local scope="$2"
    local table="$3"
    local jq_filter="$4"
    local description="$5"

    local deadline=$(( $(date -u +%s) + WAIT_TIMEOUT_SEC ))
    while true; do
        if get_table_json "${code}" "${scope}" "${table}" | jq -e "${jq_filter}" >/dev/null 2>&1; then
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
PAYMENT_REFERENCE="dfs-quote-${TIMESTAMP}"
MANIFEST_HASH="$(hash_text "dfs-manifest-${TIMESTAMP}")"
EXPIRES_AT="$(date -u -d '+1 day' +%Y-%m-%dT%H:%M:%S 2>/dev/null || python - <<'PY'
from datetime import datetime, timedelta, timezone
print((datetime.now(timezone.utc) + timedelta(days=1)).replace(microsecond=0).strftime("%Y-%m-%dT%H:%M:%S"))
PY
)"

log "Creating storage payment quote"
cleos -u "${RPC_URL}" push action "${DFS_ACCOUNT}" mkstorquote \
    "[\"${PAYMENT_REFERENCE}\",\"${DFS_PAYER_ACCOUNT}\",\"${MANIFEST_HASH}\",\"${PAYMENT_TOKEN_CONTRACT}\",\"${PAYMENT_AMOUNT}\",\"${EXPIRES_AT}\"]" \
    -p "${DFS_SETTLEMENT_ACCOUNT}@active"

wait_for_table_match \
    "${DFS_ACCOUNT}" \
    "${DFS_ACCOUNT}" \
    "storquotes" \
    ".rows[] | select(.payment_reference == \"${PAYMENT_REFERENCE}\") | select(.status == \"open\")" \
    "storage quote ${PAYMENT_REFERENCE}"

log "Funding DFS with quoted storage payment"
cleos -u "${RPC_URL}" push action "${PAYMENT_TOKEN_CONTRACT}" transfer \
    "[\"${DFS_PAYER_ACCOUNT}\",\"${DFS_ACCOUNT}\",\"${PAYMENT_AMOUNT}\",\"storage|${PAYMENT_REFERENCE}|${MANIFEST_HASH}\"]" \
    -p "${DFS_PAYER_ACCOUNT}@active"

wait_for_table_match \
    "${DFS_ACCOUNT}" \
    "${DFS_ACCOUNT}" \
    "receipts" \
    ".rows[] | select(.payment_reference == \"${PAYMENT_REFERENCE}\") | select(.status == \"received\")" \
    "DFS receipt ${PAYMENT_REFERENCE}"

wait_for_table_match \
    "${DFS_ACCOUNT}" \
    "${DFS_ACCOUNT}" \
    "storquotes" \
    ".rows[] | select(.payment_reference == \"${PAYMENT_REFERENCE}\") | select(.status == \"consumed\")" \
    "consumed storage quote ${PAYMENT_REFERENCE}"

log "Rejecting duplicate use of the same payment_reference"
if cleos -u "${RPC_URL}" push action "${PAYMENT_TOKEN_CONTRACT}" transfer \
    "[\"${DFS_PAYER_ACCOUNT}\",\"${DFS_ACCOUNT}\",\"${PAYMENT_AMOUNT}\",\"storage|${PAYMENT_REFERENCE}|${MANIFEST_HASH}\"]" \
    -p "${DFS_PAYER_ACCOUNT}@active" >/dev/null 2>&1; then
    echo "Assertion failed: duplicate storage quote payment was accepted." >&2
    exit 1
fi

log "DFS quote smoke test passed"
log "payment_reference: ${PAYMENT_REFERENCE}"
