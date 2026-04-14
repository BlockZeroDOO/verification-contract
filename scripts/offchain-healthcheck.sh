#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(cd "${script_dir}/.." && pwd)"

if [[ -n "${OFFCHAIN_ENV_FILE:-}" && -f "${OFFCHAIN_ENV_FILE}" ]]; then
    # shellcheck disable=SC1090
    source "${OFFCHAIN_ENV_FILE}"
fi

host="${OFFCHAIN_HOST:-127.0.0.1}"
ingress_port="${INGRESS_PORT:-8080}"
finality_port="${FINALITY_PORT:-8081}"
receipt_port="${RECEIPT_PORT:-8082}"
audit_port="${AUDIT_PORT:-8083}"

check_endpoint() {
    local name="$1"
    local url="$2"

    echo "[offchain-healthcheck] ${name} -> ${url}"
    curl -fsS "${url}" >/dev/null
}

check_endpoint ingress "http://${host}:${ingress_port}/healthz"
check_endpoint finality "http://${host}:${finality_port}/healthz"
check_endpoint receipt "http://${host}:${receipt_port}/healthz"
check_endpoint audit "http://${host}:${audit_port}/healthz"

echo "[offchain-healthcheck] all services are healthy"
