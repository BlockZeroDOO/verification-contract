#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(cd "${script_dir}/.." && pwd)"

if [[ -n "${OFFCHAIN_ENV_FILE:-}" && -f "${OFFCHAIN_ENV_FILE}" ]]; then
    # shellcheck disable=SC1090
    source "${OFFCHAIN_ENV_FILE}"
fi

pid_dir="${PID_DIR:-${project_root}/runtime/pids}"
log_dir="${LOG_DIR:-${project_root}/runtime/logs}"
run_script="${project_root}/scripts/run-offchain-service.sh"
host="${OFFCHAIN_HOST:-127.0.0.1}"
ingress_port="${INGRESS_PORT:-8080}"
finality_port="${FINALITY_PORT:-8081}"
receipt_port="${RECEIPT_PORT:-8082}"
audit_port="${AUDIT_PORT:-8083}"

mkdir -p "${pid_dir}" "${log_dir}"

usage() {
    echo "Usage: $0 <start|stop|restart|status>" >&2
    exit 1
}

is_running() {
    local pid_file="$1"
    [[ -f "${pid_file}" ]] && kill -0 "$(cat "${pid_file}")" >/dev/null 2>&1
}

start_service() {
    local name="$1"
    local pid_file="${pid_dir}/${name}.pid"
    local log_file="${log_dir}/${name}.log"

    if is_running "${pid_file}"; then
        echo "[offchain-stack] ${name} already running with PID $(cat "${pid_file}")"
        return
    fi

    echo "[offchain-stack] Starting ${name}"
    OFFCHAIN_ENV_FILE="${OFFCHAIN_ENV_FILE:-}" nohup "${run_script}" "${name}" >>"${log_file}" 2>&1 &
    echo $! >"${pid_file}"
}

stop_service() {
    local name="$1"
    local pid_file="${pid_dir}/${name}.pid"

    if ! is_running "${pid_file}"; then
        rm -f "${pid_file}"
        echo "[offchain-stack] ${name} is not running"
        return
    fi

    local pid
    pid="$(cat "${pid_file}")"
    echo "[offchain-stack] Stopping ${name} (PID ${pid})"
    kill "${pid}" >/dev/null 2>&1 || true
    rm -f "${pid_file}"
}

status_service() {
    local name="$1"
    local pid_file="${pid_dir}/${name}.pid"

    if is_running "${pid_file}"; then
        echo "[offchain-stack] ${name}: running (PID $(cat "${pid_file}"))"
    else
        echo "[offchain-stack] ${name}: stopped"
    fi
}

health_summary() {
    echo "[offchain-stack] health endpoints"
    echo "  ingress:  http://${host}:${ingress_port}/healthz"
    echo "  finality: http://${host}:${finality_port}/healthz"
    echo "  receipt:  http://${host}:${receipt_port}/healthz"
    echo "  audit:    http://${host}:${audit_port}/healthz"
}

command="${1:-}"
case "${command}" in
    start)
        start_service ingress
        start_service finality
        start_service receipt
        start_service audit
        health_summary
        ;;
    stop)
        stop_service audit
        stop_service receipt
        stop_service finality
        stop_service ingress
        ;;
    restart)
        "$0" stop
        "$0" start
        ;;
    status)
        status_service ingress
        status_service finality
        status_service receipt
        status_service audit
        health_summary
        ;;
    *)
        usage
        ;;
esac
