param()

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

Push-Location $projectRoot
try {
    & $python -m unittest tests.test_service_integration
}
finally {
    Pop-Location
}
