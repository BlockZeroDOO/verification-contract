param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$RemainingArgs
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$venvPython = Join-Path $projectRoot ".venv\\Scripts\\python.exe"

if (Test-Path $venvPython) {
    $pythonCommand = $venvPython
    $pythonArgs = @()
}
else {
    $pyLauncher = Get-Command py -ErrorAction SilentlyContinue
    if ($pyLauncher) {
        $pythonCommand = $pyLauncher.Source
        $pythonArgs = @("-3")
    }
    else {
        $pythonBinary = Get-Command python -ErrorAction SilentlyContinue
        if ($pythonBinary) {
            $pythonCommand = $pythonBinary.Source
            $pythonArgs = @()
        }
        else {
            $pythonCommand = $null
            $pythonArgs = @()
        }
    }
}

if (-not $pythonCommand) {
    throw "Python interpreter not found."
}

Push-Location $projectRoot
try {
    & $pythonCommand @pythonArgs "tests/live_offchain_services.py" @RemainingArgs
}
finally {
    Pop-Location
}
