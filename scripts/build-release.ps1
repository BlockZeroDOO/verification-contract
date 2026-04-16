param(
    [string[]]$ContractName = @("verif")
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot
$includeDir = Join-Path $projectRoot "include"
$ricardianDir = Join-Path $projectRoot "ricardian"

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
    $sourceArgs = @("src/$name.cpp")
    $compilerArgs = @()
    if ($name -eq "verif" -or $name -eq "verifent") {
        $sourceFile = Join-Path $projectRoot "src\verification.cpp"
        $sourceArgs = @("src/verification.cpp")
        $compilerArgs += "-DVERIFICATION_ENTERPRISE_BUILD"
        $sourceArgs += "src/verification_enterprise.cpp"
        $sourceArgs += "src/verification_core.cpp"
    }
    elseif ($name -eq "verifbill") {
        $sourceFile = Join-Path $projectRoot "src\verification_billing_entry.cpp"
        $sourceArgs = @("src/verification_billing_entry.cpp", "src/verification_billing.cpp")
    }
    elseif ($name -eq "verifretpay") {
        $sourceFile = Join-Path $projectRoot "src\verification_retail_payment_entry.cpp"
        $sourceArgs = @("src/verification_retail_payment_entry.cpp", "src/verification_retail_payment.cpp")
    }
    else {
        $sourceFile = Join-Path $projectRoot "src\$name.cpp"
    }
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
            -R $ricardianDir `
            -O3 `
            --abigen `
            --abigen_output $abiFile `
            $compilerArgs `
            $sourceArgs `
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
