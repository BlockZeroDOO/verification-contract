param(
    [string[]]$ContractName = @("verification", "dfs")
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$includeDir = Join-Path $projectRoot "include"

$compiler = Get-Command cdt-cpp -ErrorAction SilentlyContinue
if (-not $compiler) {
    $compiler = Get-Command eosio-cpp -ErrorAction SilentlyContinue
}

if (-not $compiler) {
    throw "Neither cdt-cpp nor eosio-cpp is installed or available in PATH."
}

Write-Host "Using compiler: $($compiler.Source)"
try {
    & $compiler.Source --version
}
catch {
}

foreach ($name in $ContractName) {
    $sourceFile = Join-Path $projectRoot "src\$name.cpp"
    if (-not (Test-Path $sourceFile)) {
        throw "Source file not found for contract '$name': $sourceFile"
    }

    $distDir = Join-Path $projectRoot "dist\$name"
    $wasmFile = Join-Path $distDir "$name.wasm"
    $abiFile = Join-Path $distDir "$name.abi"

    New-Item -ItemType Directory -Force -Path $distDir | Out-Null

    Write-Host "Building contract: $name"

    Push-Location $projectRoot
    try {
        & $compiler.Source `
            -I $includeDir `
            -O3 `
            --abigen `
            --abigen_output $abiFile `
            "src/$name.cpp" `
            -o $wasmFile
    }
    finally {
        Pop-Location
    }

    if (-not (Test-Path $wasmFile)) {
        throw "Expected WASM artifact was not generated: $wasmFile"
    }

    if (-not (Test-Path $abiFile)) {
        throw "Expected ABI artifact was not generated: $abiFile"
    }

    Write-Host "Build completed:"
    Write-Host "  Contract: $name"
    Write-Host "  WASM: $wasmFile"
    Write-Host "  ABI : $abiFile"
}
