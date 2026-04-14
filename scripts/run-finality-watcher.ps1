param(
    [string]$Host = "127.0.0.1",
    [int]$Port = 8081,
    [string]$RpcUrl = "https://dev-history.globalforce.io",
    [string]$StateFile = "runtime/finality-state.json",
    [int]$PollIntervalSec = 10
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $projectRoot ".venv\\Scripts\\python.exe"

if (Test-Path $venvPython) {
    $python = $venvPython
}
else {
    $python = (Get-Command python -ErrorAction SilentlyContinue)?.Source
}

if (-not $python) {
    throw "Python interpreter not found."
}

& $python (Join-Path $projectRoot "services\\finality_watcher.py") `
    --host $Host `
    --port $Port `
    --rpc-url $RpcUrl `
    --state-file $StateFile `
    --poll-interval-sec $PollIntervalSec
