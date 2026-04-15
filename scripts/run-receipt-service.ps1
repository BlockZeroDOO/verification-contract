param(
    [string]$ListenHost = "127.0.0.1",
    [int]$Port = 8082,
    [string]$StateBackend = "sqlite",
    [string]$StateFile = "runtime/finality-state.json",
    [string]$StateDb = "runtime/finality-state.sqlite3"
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

& $python (Join-Path $projectRoot "services\\receipt_service.py") `
    --host $ListenHost `
    --port $Port `
    --state-backend $StateBackend `
    --state-file $StateFile `
    --state-db $StateDb
