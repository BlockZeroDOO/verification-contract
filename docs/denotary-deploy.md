# deNotary Verification Deploy

This runbook covers deployment of the `verification` contract only.

Repository boundary:

- `C:\projects\verification-contract` owns `verification`
- `C:\projects\deNotary` owns the off-chain backend
- `C:\projects\decentralized_storage\contracts\dfs` owns the DFS contract

## Network values

- RPC URL: `https://history.denotary.io`
- chain id: `9714ab662f0899c3ac4c5a02220f3d7ab61aacae311974239cc75f22c999cc48`

## Requirements

- Linux / WSL host
- `cleos`
- `cdt-cpp`
- imported keys for `verification`
- deployed `verification` account with enough RAM/CPU/NET

## Build

```bash
./scripts/build-testnet.sh
```

Expected artifacts:

- `dist/verification/verification.wasm`
- `dist/verification/verification.abi`

## Deploy

```bash
./scripts/deploy-denotary.sh
```

Defaults:

- `RPC_URL=https://history.denotary.io`
- `DENOTARY_CHAIN_ID=9714ab662f0899c3ac4c5a02220f3d7ab61aacae311974239cc75f22c999cc48`
- `VERIFICATION_ACCOUNT=verification`
- `BUILD_BEFORE_DEPLOY=true`

Reuse already built artifacts:

```bash
BUILD_BEFORE_DEPLOY=false ./scripts/deploy-denotary.sh
```

## Manual deploy

```bash
cleos -u https://history.denotary.io set contract verification ./dist/verification -p verification@active
```

`verification` does not require `eosio.code` for the current design.

## Verify

```bash
cleos -u https://history.denotary.io get table verification verification kyc
cleos -u https://history.denotary.io get table verification verification schemas
cleos -u https://history.denotary.io get table verification verification policies
cleos -u https://history.denotary.io get table verification verification commitments
cleos -u https://history.denotary.io get table verification verification batches
```

## Smoke

```bash
export RPC_URL=https://history.denotary.io
export OWNER_ACCOUNT=verification
export VERIFICATION_ACCOUNT=verification
export SUBMITTER_ACCOUNT=youruser
./scripts/smoke-test-onchain.sh
```
