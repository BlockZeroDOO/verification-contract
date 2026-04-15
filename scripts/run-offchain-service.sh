#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(cd "${script_dir}/.." && pwd)"

if [[ -n "${OFFCHAIN_ENV_FILE:-}" && -f "${OFFCHAIN_ENV_FILE}" ]]; then
    # shellcheck disable=SC1090
    source "${OFFCHAIN_ENV_FILE}"
fi

service_name="${1:-}"
if [[ -z "${service_name}" ]]; then
    echo "Usage: $0 <ingress|finality|receipt|audit>" >&2
    exit 1
fi
shift || true

detect_python() {
    if [[ -n "${PYTHON_BIN:-}" && -x "${PYTHON_BIN}" ]]; then
        echo "${PYTHON_BIN}"
        return
    fi

    if [[ -x "${project_root}/.venv/bin/python" ]]; then
        echo "${project_root}/.venv/bin/python"
    elif command -v python3 >/dev/null 2>&1; then
        echo "python3"
    elif command -v python >/dev/null 2>&1; then
        echo "python"
    elif [[ -x "${project_root}/.venv/Scripts/python.exe" ]]; then
        echo "${project_root}/.venv/Scripts/python.exe"
    else
        echo "Python interpreter not found." >&2
        exit 1
    fi
}

python_cmd="$(detect_python)"
host="${OFFCHAIN_HOST:-127.0.0.1}"
ingress_port="${INGRESS_PORT:-8080}"
finality_port="${FINALITY_PORT:-8081}"
receipt_port="${RECEIPT_PORT:-8082}"
audit_port="${AUDIT_PORT:-8083}"
contract_account="${CONTRACT_ACCOUNT:-verification}"
rpc_url="${RPC_URL:-https://history.denotary.io}"
state_backend="${FINALITY_STATE_BACKEND:-file}"
state_file="${STATE_FILE:-${project_root}/runtime/finality-state.json}"
state_db="${FINALITY_STATE_DB:-${project_root}/runtime/finality-state.sqlite3}"
poll_interval_sec="${POLL_INTERVAL_SEC:-10}"
auth_token="${WATCHER_AUTH_TOKEN:-}"
ingress_watcher_url="${INGRESS_WATCHER_URL:-}"
ingress_watcher_auth_token="${INGRESS_WATCHER_AUTH_TOKEN:-${WATCHER_AUTH_TOKEN:-}}"
ingress_watcher_rpc_url="${INGRESS_WATCHER_RPC_URL:-${RPC_URL:-https://history.denotary.io}}"

mkdir -p "$(dirname "${state_file}")"
mkdir -p "$(dirname "${state_db}")"

case "${service_name}" in
    ingress)
        args=(
            "${project_root}/services/ingress_api.py"
            --host "${host}"
            --port "${ingress_port}"
            --contract-account "${contract_account}"
        )
        if [[ -n "${ingress_watcher_url}" ]]; then
            args+=(--watcher-url "${ingress_watcher_url}")
            if [[ -n "${ingress_watcher_auth_token}" ]]; then
                args+=(--watcher-auth-token "${ingress_watcher_auth_token}")
            fi
            if [[ -n "${ingress_watcher_rpc_url}" ]]; then
                args+=(--watcher-rpc-url "${ingress_watcher_rpc_url}")
            fi
        fi
        exec "${python_cmd}" "${args[@]}" "$@"
        ;;
    finality)
        if [[ -z "${auth_token}" ]]; then
            echo "WATCHER_AUTH_TOKEN is required to start the finality watcher." >&2
            exit 1
        fi
        args=(
            "${project_root}/services/finality_watcher.py"
            --host "${host}"
            --port "${finality_port}"
            --rpc-url "${rpc_url}"
            --state-backend "${state_backend}"
            --state-file "${state_file}"
            --state-db "${state_db}"
            --poll-interval-sec "${poll_interval_sec}"
            --auth-token "${auth_token}"
        )
        exec "${python_cmd}" "${args[@]}" "$@"
        ;;
    receipt)
        exec "${python_cmd}" "${project_root}/services/receipt_service.py" \
            --host "${host}" \
            --port "${receipt_port}" \
            --state-backend "${state_backend}" \
            --state-file "${state_file}" \
            --state-db "${state_db}" \
            "$@"
        ;;
    audit)
        exec "${python_cmd}" "${project_root}/services/audit_api.py" \
            --host "${host}" \
            --port "${audit_port}" \
            --state-backend "${state_backend}" \
            --state-file "${state_file}" \
            --state-db "${state_db}" \
            "$@"
        ;;
    *)
        echo "Unsupported service '${service_name}'." >&2
        exit 1
        ;;
esac
