param(
    [string]$Host = "127.0.0.1",
    [int]$Port = 8082,
    [string]$StateFile = "runtime/finality-state.json"
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

& $python (Join-Path $projectRoot "services\\receipt_service.py") `
    --host $Host `
    --port $Port `
    --state-file $StateFile
