# Jungle4 Verification Deploy

This runbook covers deployment of the `verification` contract only on Jungle4.

Repository boundary:

- `C:\projects\verification-contract` owns `verification`
- `C:\projects\deNotary` owns the off-chain backend
- `C:\projects\decentralized_storage\contracts\dfs` owns the DFS contract

## Network values

- RPC URL: `https://jungle4.api.eosnation.io`
- chain id: `73e4385a2708e6d7048834fbc1079f2fabb17b3c125b146af438971e90716c4d`

## Requirements

- Linux / WSL host
- `cleos`
- `cdt-cpp`
- imported keys for `verification`
- deployed Jungle4 `verification` account with enough RAM/CPU/NET

## Build

```bash
./scripts/build-testnet.sh
```

Expected artifacts:

- `dist/verification/verification.wasm`
- `dist/verification/verification.abi`

## Deploy

```bash
./scripts/deploy-jungle4.sh
```

Defaults:

- `RPC_URL=https://jungle4.api.eosnation.io`
- `VERIFICATION_ACCOUNT=verification`
- `BUILD_BEFORE_DEPLOY=true`

## Manual deploy

```bash
cleos -u https://jungle4.api.eosnation.io set contract verification ./dist/verification -p verification@active
```

## Verify

```bash
cleos -u https://jungle4.api.eosnation.io get table verification verification kyc
cleos -u https://jungle4.api.eosnation.io get table verification verification schemas
cleos -u https://jungle4.api.eosnation.io get table verification verification policies
cleos -u https://jungle4.api.eosnation.io get table verification verification commitments
cleos -u https://jungle4.api.eosnation.io get table verification verification batches
```

## Smoke

```bash
export OWNER_ACCOUNT=verification
export VERIFICATION_ACCOUNT=verification
export SUBMITTER_ACCOUNT=youruser
./scripts/smoke-test-jungle4.sh
```
