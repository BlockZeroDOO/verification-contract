param(
    [string]$ListenHost = "127.0.0.1",
    [int]$Port = 8080,
    [string]$ContractAccount = "verification",
    [string]$WatcherUrl = "",
    [string]$WatcherAuthToken = "",
    [string]$WatcherRpcUrl = ""
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

$argsList = @(
    (Join-Path $projectRoot "services\\ingress_api.py"),
    "--host", $ListenHost,
    "--port", $Port,
    "--contract-account", $ContractAccount
)

if ($WatcherUrl) {
    $argsList += @("--watcher-url", $WatcherUrl)
}

if ($WatcherAuthToken) {
    $argsList += @("--watcher-auth-token", $WatcherAuthToken)
}

if ($WatcherRpcUrl) {
    $argsList += @("--watcher-rpc-url", $WatcherRpcUrl)
}

& $python @argsList
