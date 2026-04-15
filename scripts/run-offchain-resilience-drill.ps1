param(
    [string]$RpcUrl = $(if ($env:RPC_URL) { $env:RPC_URL } else { "https://history.denotary.io" }),
    [string]$ExpectedChainId = $(if ($env:EXPECTED_CHAIN_ID) { $env:EXPECTED_CHAIN_ID } else { "9714ab662f0899c3ac4c5a02220f3d7ab61aacae311974239cc75f22c999cc48" }),
    [string]$NetworkLabel = $(if ($env:NETWORK_LABEL) { $env:NETWORK_LABEL } else { "deNotary" }),
    [string]$OwnerAccount = $(if ($env:OWNER_ACCOUNT) { $env:OWNER_ACCOUNT } else { "verification" }),
    [string]$SubmitterAccount = $(if ($env:SUBMITTER_ACCOUNT) { $env:SUBMITTER_ACCOUNT } else { "verification" }),
    [string]$WatcherAuthToken = $(if ($env:WATCHER_AUTH_TOKEN) { $env:WATCHER_AUTH_TOKEN } else { "" }),
    [string]$ComposeFile = $(if ($env:COMPOSE_FILE) { $env:COMPOSE_FILE } else { "docker-compose.offchain.yml" }),
    [string]$ComposeEnvFile = $(if ($env:COMPOSE_ENV_FILE) { $env:COMPOSE_ENV_FILE } else { "config/offchain.compose.resilience.env.example" }),
    [string]$ComposeProjectDir = $(if ($env:COMPOSE_PROJECT_DIR) { $env:COMPOSE_PROJECT_DIR } else { (Get-Location).Path }),
    [string]$DumpDir = $(if ($env:DUMP_DIR) { $env:DUMP_DIR } else { "runtime/live-offchain-resilience-logs" })
)

if (-not $WatcherAuthToken) {
    throw "WATCHER_AUTH_TOKEN is required for the resilience drill."
}

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$runner = Join-Path $scriptDir "run-live-offchain-services.ps1"

& $runner `
    -UseExternalServices `
    -ComposeFile $ComposeFile `
    -ComposeEnvFile $ComposeEnvFile `
    -ComposeProjectDir $ComposeProjectDir `
    -RpcUrl $RpcUrl `
    -ExpectedChainId $ExpectedChainId `
    -NetworkLabel $NetworkLabel `
    -OwnerAccount $OwnerAccount `
    -SubmitterAccount $SubmitterAccount `
    -WatcherAuthToken $WatcherAuthToken `
    -DumpDir $DumpDir

if ($LASTEXITCODE -ne 0) {
    exit $LASTEXITCODE
}
