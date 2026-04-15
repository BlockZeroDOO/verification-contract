#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(cd "${script_dir}/.." && pwd)"

rpc_url="${RPC_URL:-https://history.denotary.io}"
expected_chain_id="${EXPECTED_CHAIN_ID:-9714ab662f0899c3ac4c5a02220f3d7ab61aacae311974239cc75f22c999cc48}"
network_label="${NETWORK_LABEL:-deNotary}"
owner_account="${OWNER_ACCOUNT:-verification}"
submitter_account="${SUBMITTER_ACCOUNT:-verification}"
watcher_auth_token="${WATCHER_AUTH_TOKEN:-}"
compose_file="${COMPOSE_FILE:-docker-compose.offchain.yml}"
compose_env_file="${COMPOSE_ENV_FILE:-config/offchain.compose.resilience.env.example}"
compose_project_dir="${COMPOSE_PROJECT_DIR:-${project_root}}"
dump_dir="${DUMP_DIR:-runtime/live-offchain-resilience-logs}"

if [[ -z "${watcher_auth_token}" ]]; then
    echo "WATCHER_AUTH_TOKEN is required for the resilience drill." >&2
    exit 1
fi

if [[ ! -f "${project_root}/${compose_file}" && ! -f "${compose_file}" ]]; then
    echo "Compose file not found: ${compose_file}" >&2
    exit 1
fi

if [[ ! -f "${project_root}/${compose_env_file}" && ! -f "${compose_env_file}" ]]; then
    echo "Compose env file not found: ${compose_env_file}" >&2
    exit 1
fi

exec "${script_dir}/run-live-offchain-services.sh" \
    --use-external-services \
    --compose-file "${compose_file}" \
    --compose-env-file "${compose_env_file}" \
    --compose-project-dir "${compose_project_dir}" \
    --rpc-url "${rpc_url}" \
    --expected-chain-id "${expected_chain_id}" \
    --network-label "${network_label}" \
    --owner-account "${owner_account}" \
    --submitter-account "${submitter_account}" \
    --watcher-auth-token "${watcher_auth_token}" \
    --dump-dir "${dump_dir}" \
    "$@"
