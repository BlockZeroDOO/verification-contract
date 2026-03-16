param(
    [string]$ContractName = "verification"
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$sourceFile = Join-Path $projectRoot "src\verification.cpp"
$includeDir = Join-Path $projectRoot "include"
$distDir = Join-Path $projectRoot "dist\$ContractName"
$wasmFile = Join-Path $distDir "$ContractName.wasm"

$compiler = Get-Command cdt-cpp -ErrorAction SilentlyContinue
if (-not $compiler) {
    $compiler = Get-Command eosio-cpp -ErrorAction SilentlyContinue
}

if (-not $compiler) {
    throw "Neither cdt-cpp nor eosio-cpp is installed or available in PATH."
}

New-Item -ItemType Directory -Force -Path $distDir | Out-Null

Push-Location $projectRoot
try {
    & $compiler.Source `
        -I $includeDir `
        -O3 `
        --abigen `
        "src/verification.cpp" `
        -o $wasmFile
}
finally {
    Pop-Location
}

Write-Host "Build completed:"
Write-Host "  WASM: $wasmFile"
Write-Host "  ABI : $(Join-Path $distDir "$ContractName.abi")"
