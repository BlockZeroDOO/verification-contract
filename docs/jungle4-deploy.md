# Jungle4 Deploy

This runbook keeps `jungletestnet.io` available as an optional external test network for the current DeNotary contract model.

Current scope on Jungle4:

- `verification`
- `dfs`

This runbook does not use the older `managementel -> verification` flow.

## Network values

- RPC URL: `https://jungle4.api.eosnation.io`
- chain id: `73e4385a2708e6d7048834fbc1079f2fabb17b3c125b146af438971e90716c4d`

Useful ecosystem links:

- https://jungletestnet.io/
- https://monitor.jungletestnet.io/

## What you need

- Linux or WSL host with `cleos`
- `cdt-cpp`
- deployed Jungle4 accounts with RAM/CPU/NET
- imported keys for the contract accounts

Recommended account layout:

- `verification`
- `dfs`

## Build

```bash
./scripts/build-testnet.sh
```

Expected artifacts:

- `dist/verification/verification.wasm`
- `dist/verification/verification.abi`
- `dist/dfs/dfs.wasm`
- `dist/dfs/dfs.abi`

## Deploy with the wrapper

```bash
chmod +x ./scripts/deploy-jungle4.sh
./scripts/deploy-jungle4.sh
```

Defaults:

- `RPC_URL=https://jungle4.api.eosnation.io`
- `VERIFICATION_ACCOUNT=verification`
- `DFS_ACCOUNT=dfs`
- `DEPLOY_DFS=true`
- `BUILD_BEFORE_DEPLOY=true`

Deploy only `verification`:

```bash
DEPLOY_DFS=false ./scripts/deploy-jungle4.sh
```

## Manual deploy commands

```bash
cleos -u https://jungle4.api.eosnation.io set contract verification ./dist/verification -p verification@active
cleos -u https://jungle4.api.eosnation.io set contract dfs ./dist/dfs -p dfs@active
cleos -u https://jungle4.api.eosnation.io set account permission dfs active --add-code -p dfs@active
```

`verification` does not need `eosio.code` for the current design.

## On-chain smoke test

```bash
export OWNER_ACCOUNT=verification
export VERIFICATION_ACCOUNT=verification
export SUBMITTER_ACCOUNT=youruser
./scripts/smoke-test-jungle4.sh
```

## Live-chain integration test

```bash
export OWNER_ACCOUNT=verification
export SUBMITTER_ACCOUNT=youruser
./scripts/run-live-chain-integration.sh \
  --rpc-url https://jungle4.api.eosnation.io \
  --expected-chain-id 73e4385a2708e6d7048834fbc1079f2fabb17b3c125b146af438971e90716c4d \
  --network-label Jungle4 \
  --owner-account "${OWNER_ACCOUNT}" \
  --submitter-account "${SUBMITTER_ACCOUNT}"
```

## Verify on-chain state

```bash
cleos -u https://jungle4.api.eosnation.io get table verification verification kyc
cleos -u https://jungle4.api.eosnation.io get table verification verification schemas
cleos -u https://jungle4.api.eosnation.io get table verification verification policies
cleos -u https://jungle4.api.eosnation.io get table verification verification commitments
cleos -u https://jungle4.api.eosnation.io get table verification verification batches
cleos -u https://jungle4.api.eosnation.io get table dfs dfs pricepolicy
cleos -u https://jungle4.api.eosnation.io get table dfs dfs acpttokens
```

## Notes

- treat Jungle4 as an optional public test environment
- the primary target chain for the project remains `deNotary.io`
- for the active chain, use [docs/denotary-deploy.md](/c:/projects/verification-contract/docs/denotary-deploy.md:1)
