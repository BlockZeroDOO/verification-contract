param(
    [bool]$BuildBeforeDryRun = $true,
    [ValidateSet("release", "testnet")]
    [string]$BuildProfile = "release",
    [string[]]$BuildTargets = @("verification", "dfs"),
    [bool]$RunServiceIntegration = $true,
    [bool]$RunLiveChainIntegration = $false,
    [bool]$RunOnchainSmoke = $false,
    [string]$RpcUrl = "https://history.denotary.io",
    [string]$ExpectedChainId = "9714ab662f0899c3ac4c5a02220f3d7ab61aacae311974239cc75f22c999cc48",
    [string]$NetworkLabel = "deNotary.io",
    [string]$OwnerAccount = "",
    [string]$SubmitterAccount = "",
    [string]$VerificationAccount = "verification",
    [string]$WatcherAuthToken = ""
)

$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $PSScriptRoot

function Invoke-Step {
    param(
        [string]$Message,
        [scriptblock]$Script
    )

    Write-Host "[rollout-dry-run] $Message"
    & $Script
}

if ($BuildBeforeDryRun) {
    if ($BuildProfile -eq "release") {
        Invoke-Step "Building release artifacts" {
            & (Join-Path $projectRoot "scripts\\build-release.ps1") -ContractName $BuildTargets
        }
    }
    else {
        Invoke-Step "Building testnet artifacts" {
            & (Join-Path $projectRoot "scripts\\build-testnet.ps1") -ContractName $BuildTargets
        }
    }
}

if ($RunServiceIntegration) {
    Invoke-Step "Running local service integration suite" {
        & (Join-Path $projectRoot "scripts\\run-integration-tests.ps1")
    }
}

if ($RunLiveChainIntegration) {
    if (-not $OwnerAccount) {
        throw "OwnerAccount is required for live-chain dry-run."
    }
    if (-not $SubmitterAccount) {
        throw "SubmitterAccount is required for live-chain dry-run."
    }

    $arguments = @(
        "--rpc-url", $RpcUrl,
        "--expected-chain-id", $ExpectedChainId,
        "--network-label", $NetworkLabel,
        "--owner-account", $OwnerAccount,
        "--submitter-account", $SubmitterAccount
    )
    if ($WatcherAuthToken) {
        $arguments += @("--watcher-auth-token", $WatcherAuthToken)
    }

    Invoke-Step "Running live-chain integration suite" {
        & (Join-Path $projectRoot "scripts\\run-live-chain-integration.ps1") @arguments
    }
}

if ($RunOnchainSmoke) {
    if (-not $OwnerAccount) {
        throw "OwnerAccount is required for on-chain smoke."
    }
    if (-not $SubmitterAccount) {
        throw "SubmitterAccount is required for on-chain smoke."
    }

    Invoke-Step "Running on-chain smoke suite" {
        $env:RPC_URL = $RpcUrl
        $env:OWNER_ACCOUNT = $OwnerAccount
        $env:VERIFICATION_ACCOUNT = $VerificationAccount
        $env:SUBMITTER_ACCOUNT = $SubmitterAccount
        try {
            bash (Join-Path $projectRoot "scripts/smoke-test-onchain.sh")
        }
        finally {
            Remove-Item Env:RPC_URL -ErrorAction SilentlyContinue
            Remove-Item Env:OWNER_ACCOUNT -ErrorAction SilentlyContinue
            Remove-Item Env:VERIFICATION_ACCOUNT -ErrorAction SilentlyContinue
            Remove-Item Env:SUBMITTER_ACCOUNT -ErrorAction SilentlyContinue
        }
    }
}

Write-Host ""
Write-Host "rollout dry-run completed."
Write-Host ""
Write-Host "build before dry-run: $BuildBeforeDryRun"
Write-Host "build profile: $BuildProfile"
Write-Host "service integration: $RunServiceIntegration"
Write-Host "live-chain integration: $RunLiveChainIntegration"
Write-Host "on-chain smoke: $RunOnchainSmoke"
Write-Host "network: $NetworkLabel"
Write-Host "rpc url: $RpcUrl"
