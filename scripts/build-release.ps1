param(
    [string]$ContractName = "verification"
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$sourceFile = Join-Path $projectRoot "src\verification.cpp"
$includeDir = Join-Path $projectRoot "include"
$distDir = Join-Path $projectRoot "dist\$ContractName"
$wasmFile = Join-Path $distDir "$ContractName.wasm"
$abiFile = Join-Path $distDir "$ContractName.abi"

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

$hasGetFileHash = Get-Command Get-FileHash -ErrorAction SilentlyContinue
if ($hasGetFileHash) {
    $wasmHash = (Get-FileHash -Algorithm SHA256 -Path $wasmFile).Hash.ToLowerInvariant()
    $abiHash = (Get-FileHash -Algorithm SHA256 -Path $abiFile).Hash.ToLowerInvariant()

    Set-Content -Path "$wasmFile.sha256" -Value "$wasmHash  $(Split-Path -Leaf $wasmFile)"
    Set-Content -Path "$abiFile.sha256" -Value "$abiHash  $(Split-Path -Leaf $abiFile)"
}

Write-Host "Release build completed:"
Write-Host "  WASM: $wasmFile"
Write-Host "  ABI : $abiFile"
if ($hasGetFileHash) {
    Write-Host "  SHA256: $wasmFile.sha256"
    Write-Host "  SHA256: $abiFile.sha256"
}
