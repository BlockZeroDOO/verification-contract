param(
    [string[]]$ContractName = @("verification", "managementel", "dfs")
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

foreach ($name in $ContractName) {
    $sourceFile = Join-Path $projectRoot "src\$name.cpp"
    if (-not (Test-Path $sourceFile)) {
        throw "Source file not found for contract '$name': $sourceFile"
    }

    $distDir = Join-Path $projectRoot "dist\$name"
    $wasmFile = Join-Path $distDir "$name.wasm"

    New-Item -ItemType Directory -Force -Path $distDir | Out-Null

    Push-Location $projectRoot
    try {
        & $compiler.Source `
            -I $includeDir `
            -O3 `
            --abigen `
            "src/$name.cpp" `
            -o $wasmFile
    }
    finally {
        Pop-Location
    }

    Write-Host "Build completed:"
    Write-Host "  Contract: $name"
    Write-Host "  WASM: $wasmFile"
    Write-Host "  ABI : $(Join-Path $distDir "$name.abi")"
}
