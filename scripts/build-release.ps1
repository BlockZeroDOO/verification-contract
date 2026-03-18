param(
    [string[]]$ContractName = @("verification", "managementel")
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
    $abiFile = Join-Path $distDir "$name.abi"

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

    $hasGetFileHash = Get-Command Get-FileHash -ErrorAction SilentlyContinue
    if ($hasGetFileHash) {
        $wasmHash = (Get-FileHash -Algorithm SHA256 -Path $wasmFile).Hash.ToLowerInvariant()
        $abiHash = (Get-FileHash -Algorithm SHA256 -Path $abiFile).Hash.ToLowerInvariant()

        Set-Content -Path "$wasmFile.sha256" -Value "$wasmHash  $(Split-Path -Leaf $wasmFile)"
        Set-Content -Path "$abiFile.sha256" -Value "$abiHash  $(Split-Path -Leaf $abiFile)"
    }

    Write-Host "Release build completed:"
    Write-Host "  Contract: $name"
    Write-Host "  WASM: $wasmFile"
    Write-Host "  ABI : $abiFile"
    if ($hasGetFileHash) {
        Write-Host "  SHA256: $wasmFile.sha256"
        Write-Host "  SHA256: $abiFile.sha256"
    }
}
