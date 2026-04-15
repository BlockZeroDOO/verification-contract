param(
    [string]$ListenHost = "127.0.0.1",
    [int]$Port = 8081,
    [string]$RpcUrl = "https://history.denotary.io",
    [string]$StateBackend = "file",
    [string]$StateFile = "runtime/finality-state.json",
    [string]$StateDb = "runtime/finality-state.sqlite3",
    [int]$PollIntervalSec = 10,
    [string]$AuthToken = ""
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $projectRoot ".venv\\Scripts\\python.exe"

if (Test-Path $venvPython) {
    $python = $venvPython
}
else {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        $python = $pythonCommand.Source
    }
    else {
        $python = $null
    }
}

if (-not $python) {
    throw "Python interpreter not found."
}

$arguments = @(
    (Join-Path $projectRoot "services\\finality_watcher.py"),
    "--host", $ListenHost,
    "--port", $Port,
    "--rpc-url", $RpcUrl,
    "--state-backend", $StateBackend,
    "--state-file", $StateFile,
    "--state-db", $StateDb,
    "--poll-interval-sec", $PollIntervalSec
)

if ($AuthToken) {
    $arguments += @("--auth-token", $AuthToken)
}

& $python @arguments
