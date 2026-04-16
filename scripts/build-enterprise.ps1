param()

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
& (Join-Path $scriptDir "build-testnet.ps1") -ContractName verif
