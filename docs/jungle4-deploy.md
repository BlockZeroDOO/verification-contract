# Jungle4 Verification Deploy

This runbook covers deployment of the `verifent` contract only on Jungle4.

Repository boundary:

- `C:\projects\verification-contract` owns `verifent`
- `C:\projects\deNotary` owns the off-chain backend
- `C:\projects\decentralized_storage\contracts\dfs` owns the DFS contract

## Network values

- RPC URL: `https://jungle4.api.eosnation.io`
- chain id: `73e4385a2708e6d7048834fbc1079f2fabb17b3c125b146af438971e90716c4d`

## Requirements

- Linux / WSL host
- `cleos`
- `cdt-cpp`
- imported keys for `verifent`
- deployed Jungle4 `verifent` account with enough RAM/CPU/NET

## Build

```bash
./scripts/build-testnet.sh
```

Expected artifacts:

- `dist/verifent/verifent.wasm`
- `dist/verifent/verifent.abi`

## Deploy

```bash
./scripts/deploy-jungle4.sh
```

Defaults:

- `RPC_URL=https://jungle4.api.eosnation.io`
- `VERIFICATION_ACCOUNT=verifent`
- `BUILD_BEFORE_DEPLOY=true`

## Manual deploy

```bash
cleos -u https://jungle4.api.eosnation.io set contract verifent ./dist/verifent -p verifent@active
```

## Verify

```bash
cleos -u https://jungle4.api.eosnation.io get table verifent verifent kyc
cleos -u https://jungle4.api.eosnation.io get table verifent verifent schemas
cleos -u https://jungle4.api.eosnation.io get table verifent verifent policies
cleos -u https://jungle4.api.eosnation.io get table verifent verifent commitments
cleos -u https://jungle4.api.eosnation.io get table verifent verifent batches
```

## Smoke

```bash
export OWNER_ACCOUNT=verifent
export VERIFICATION_ACCOUNT=verifent
export SUBMITTER_ACCOUNT=youruser
./scripts/smoke-test-jungle4.sh
```
