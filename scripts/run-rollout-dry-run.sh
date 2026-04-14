#!/usr/bin/env bash

set -euo pipefail

script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
project_root="$(cd "${script_dir}/.." && pwd)"

BUILD_BEFORE_DRY_RUN="${BUILD_BEFORE_DRY_RUN:-true}"
BUILD_PROFILE="${BUILD_PROFILE:-release}"
BUILD_TARGETS="${BUILD_TARGETS:-verification dfs}"
RUN_SERVICE_INTEGRATION="${RUN_SERVICE_INTEGRATION:-true}"
RUN_LIVE_CHAIN_INTEGRATION="${RUN_LIVE_CHAIN_INTEGRATION:-false}"
RUN_ONCHAIN_SMOKE="${RUN_ONCHAIN_SMOKE:-false}"
RPC_URL="${RPC_URL:-https://history.denotary.io}"
EXPECTED_CHAIN_ID="${EXPECTED_CHAIN_ID:-9714ab662f0899c3ac4c5a02220f3d7ab61aacae311974239cc75f22c999cc48}"
NETWORK_LABEL="${NETWORK_LABEL:-deNotary.io}"
WATCHER_AUTH_TOKEN="${WATCHER_AUTH_TOKEN:-}"

log() {
    printf '[rollout-dry-run] %s\n' "$1"
}

run_step() {
    log "$1"
    shift
    "$@"
}

if [[ "${BUILD_BEFORE_DRY_RUN}" == "true" ]]; then
    if [[ "${BUILD_PROFILE}" == "release" ]]; then
        run_step "Building release artifacts" bash "${project_root}/scripts/build-release.sh" ${BUILD_TARGETS}
    elif [[ "${BUILD_PROFILE}" == "testnet" ]]; then
        run_step "Building testnet artifacts" bash "${project_root}/scripts/build-testnet.sh" ${BUILD_TARGETS}
    else
        echo "Unsupported BUILD_PROFILE='${BUILD_PROFILE}'. Use 'release' or 'testnet'." >&2
        exit 1
    fi
fi

if [[ "${RUN_SERVICE_INTEGRATION}" == "true" ]]; then
    run_step "Running local service integration suite" bash "${project_root}/scripts/run-integration-tests.sh"
fi

if [[ "${RUN_LIVE_CHAIN_INTEGRATION}" == "true" ]]; then
    : "${OWNER_ACCOUNT:?Set OWNER_ACCOUNT for live-chain dry-run.}"
    : "${SUBMITTER_ACCOUNT:?Set SUBMITTER_ACCOUNT for live-chain dry-run.}"

    live_args=(
        "--rpc-url" "${RPC_URL}"
        "--expected-chain-id" "${EXPECTED_CHAIN_ID}"
        "--network-label" "${NETWORK_LABEL}"
        "--owner-account" "${OWNER_ACCOUNT}"
        "--submitter-account" "${SUBMITTER_ACCOUNT}"
    )

    if [[ -n "${WATCHER_AUTH_TOKEN}" ]]; then
        live_args+=("--watcher-auth-token" "${WATCHER_AUTH_TOKEN}")
    fi

    run_step "Running live-chain integration suite" bash "${project_root}/scripts/run-live-chain-integration.sh" "${live_args[@]}"
fi

if [[ "${RUN_ONCHAIN_SMOKE}" == "true" ]]; then
    : "${OWNER_ACCOUNT:?Set OWNER_ACCOUNT for on-chain smoke.}"
    : "${SUBMITTER_ACCOUNT:?Set SUBMITTER_ACCOUNT for on-chain smoke.}"

    smoke_env=(
        "RPC_URL=${RPC_URL}"
        "OWNER_ACCOUNT=${OWNER_ACCOUNT}"
        "VERIFICATION_ACCOUNT=${VERIFICATION_ACCOUNT:-verification}"
        "SUBMITTER_ACCOUNT=${SUBMITTER_ACCOUNT}"
    )

    log "Running on-chain smoke suite"
    env "${smoke_env[@]}" bash "${project_root}/scripts/smoke-test-onchain.sh"
fi

cat <<EOF

rollout dry-run completed.

build before dry-run: ${BUILD_BEFORE_DRY_RUN}
build profile: ${BUILD_PROFILE}
service integration: ${RUN_SERVICE_INTEGRATION}
live-chain integration: ${RUN_LIVE_CHAIN_INTEGRATION}
on-chain smoke: ${RUN_ONCHAIN_SMOKE}
network: ${NETWORK_LABEL}
rpc url: ${RPC_URL}

EOF
