param(
    [string]$ListenHost = "127.0.0.1",
    [int]$Port = 8080,
    [string]$ContractAccount = "verification"
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

& $python (Join-Path $projectRoot "services\\ingress_api.py") `
    --host $ListenHost `
    --port $Port `
    --contract-account $ContractAccount
