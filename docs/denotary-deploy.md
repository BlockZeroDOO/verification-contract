# deNotary Chain Deploy

This runbook targets the active `deNotary.io` chain.

Network values:

- history / RPC URL: `https://history.denotary.io`
- chain id: `9714ab662f0899c3ac4c5a02220f3d7ab61aacae311974239cc75f22c999cc48`

Current contract scope in this repository:

- `verification`
- `dfs`

Legacy `managementel` deployment flow is no longer part of the active DeNotary chain model.

## What you need on Linux

- Debian/Ubuntu-compatible Linux host on `amd64`
- `cleos`
- `cdt-cpp`
- imported keys for the target contract accounts
- deployed accounts with enough RAM/CPU/NET

Recommended account layout:

- `verification`
- `dfs`

## Install toolchain on Linux

```bash
chmod +x ./scripts/bootstrap-linux-antelope.sh
./scripts/bootstrap-linux-antelope.sh
```

## Build the contracts

```bash
chmod +x ./scripts/build-testnet.sh
./scripts/build-testnet.sh
```

Expected artifacts:

- `dist/verification/verification.wasm`
- `dist/verification/verification.abi`
- `dist/dfs/dfs.wasm`
- `dist/dfs/dfs.abi`

## Deploy to deNotary

The deploy script validates the chain id, verifies that the required accounts exist, builds artifacts by default, deploys contracts, and enables `eosio.code` where needed.

```bash
chmod +x ./scripts/deploy-denotary.sh
./scripts/deploy-denotary.sh
```

Defaults:

- `RPC_URL=https://history.denotary.io`
- `DENOTARY_CHAIN_ID=9714ab662f0899c3ac4c5a02220f3d7ab61aacae311974239cc75f22c999cc48`
- `VERIFICATION_ACCOUNT=verification`
- `DFS_ACCOUNT=dfs`
- `DEPLOY_DFS=true`
- `BUILD_BEFORE_DEPLOY=true`

Examples:

Deploy only `verification`:

```bash
DEPLOY_DFS=false ./scripts/deploy-denotary.sh
```

Reuse already built artifacts:

```bash
BUILD_BEFORE_DEPLOY=false ./scripts/deploy-denotary.sh
```

## Manual deploy commands

```bash
cleos -u https://history.denotary.io set contract verification ./dist/verification -p verification@active
cleos -u https://history.denotary.io set contract dfs ./dist/dfs -p dfs@active
cleos -u https://history.denotary.io set account permission dfs active --add-code -p dfs@active
```

`verification` does not require `eosio.code` for the current design.

## Smoke tests

On-chain anchoring smoke:

```bash
export RPC_URL=https://history.denotary.io
export OWNER_ACCOUNT=verification
export VERIFICATION_ACCOUNT=verification
export SUBMITTER_ACCOUNT=youruser
./scripts/smoke-test-onchain.sh
```

Legacy paid-proof smoke wrapper, if still needed for the old proof flow:

```bash
export OWNER_ACCOUNT=verification
export VERIFICATION_ACCOUNT=verification
export PAYER_ACCOUNT=yourpayer
./scripts/smoke-test-denotary.sh
```

## Verify on-chain state

```bash
cleos -u https://history.denotary.io get table verification verification kyc
cleos -u https://history.denotary.io get table verification verification schemas
cleos -u https://history.denotary.io get table verification verification policies
cleos -u https://history.denotary.io get table verification verification commitments
cleos -u https://history.denotary.io get table verification verification batches
cleos -u https://history.denotary.io get table dfs dfs pricepolicy
cleos -u https://history.denotary.io get table dfs dfs acpttokens
```

## DFS follow-up

If you deploy `dfs`, finish its token and policy bootstrap with:

- [docs/dfs-testnet-bootstrap.md](/c:/projects/verification-contract/docs/dfs-testnet-bootstrap.md:1)

## Optional external testnet

If you want a public external test environment in addition to the main DeNotary chain, use:

- [docs/jungle4-deploy.md](/c:/projects/verification-contract/docs/jungle4-deploy.md:1)
