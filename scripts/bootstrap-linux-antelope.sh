#!/usr/bin/env bash

set -euo pipefail

if [[ "$(uname -s)" != "Linux" ]]; then
    echo "bootstrap-linux-antelope.sh must be run on Linux." >&2
    exit 1
fi

if [[ "$(uname -m)" != "x86_64" && "$(uname -m)" != "amd64" ]]; then
    echo "This installer currently supports only amd64/x86_64 Linux hosts." >&2
    exit 1
fi

if ! command -v apt-get >/dev/null 2>&1; then
    echo "This installer currently supports Debian/Ubuntu systems with apt-get." >&2
    exit 1
fi

run_privileged() {
    if [[ "${EUID}" -eq 0 ]]; then
        "$@"
        return
    fi

    if command -v sudo >/dev/null 2>&1; then
        sudo "$@"
        return
    fi

    echo "This step requires root privileges. Re-run as root or install sudo." >&2
    exit 1
}

fetch_latest_asset_url() {
    local repo="$1"
    local asset_pattern="$2"

    curl -fsSL "https://api.github.com/repos/${repo}/releases/latest" \
        | jq -r --arg asset_pattern "${asset_pattern}" '.assets[] | select(.name | test($asset_pattern)) | .browser_download_url' \
        | head -n 1
}

echo "[bootstrap] Installing base packages"
run_privileged apt-get update
run_privileged apt-get install -y ca-certificates curl git jq lsb-release

leap_url="$(fetch_latest_asset_url "AntelopeIO/leap" "^leap_.*_amd64\\.deb$")"
cdt_url="$(fetch_latest_asset_url "AntelopeIO/cdt" "^cdt_.*_amd64\\.deb$")"

if [[ -z "${leap_url}" ]]; then
    echo "Could not resolve Antelope Leap .deb asset from GitHub releases." >&2
    exit 1
fi

if [[ -z "${cdt_url}" ]]; then
    echo "Could not resolve Antelope CDT .deb asset from GitHub releases." >&2
    exit 1
fi

tmp_dir="$(mktemp -d)"
trap 'rm -rf "${tmp_dir}"' EXIT

leap_deb="${tmp_dir}/$(basename "${leap_url}")"
cdt_deb="${tmp_dir}/$(basename "${cdt_url}")"

echo "[bootstrap] Downloading ${leap_url}"
curl -fL "${leap_url}" -o "${leap_deb}"

echo "[bootstrap] Downloading ${cdt_url}"
curl -fL "${cdt_url}" -o "${cdt_deb}"

echo "[bootstrap] Installing Leap and CDT"
run_privileged dpkg -i "${leap_deb}" "${cdt_deb}" || true
run_privileged apt-get install -f -y

if ! command -v cleos >/dev/null 2>&1; then
    echo "cleos was not found in PATH after installing Leap." >&2
    exit 1
fi

if ! command -v cdt-cpp >/dev/null 2>&1; then
    echo "cdt-cpp was not found in PATH after installing CDT." >&2
    exit 1
fi

echo "[bootstrap] cleos: $(command -v cleos)"
cleos version client || true

echo "[bootstrap] cdt-cpp: $(command -v cdt-cpp)"
cdt-cpp --version || true

cat <<'EOF'

Linux bootstrap completed.

Next steps:
  1. Import your Jungle4 deployment keys into cleos wallet.
  2. Build the contracts with ./scripts/build-testnet.sh
  3. Deploy with ./scripts/deploy-jungle4.sh

EOF
