# Jungle4 Deploy

> Legacy note: this guide still describes the old `managementel -> verification` flow.
> The current codebase accepts paid submissions directly in `verification`; use `README.md`
> and the updated scripts as the source of truth until this document is rewritten.

This runbook prepares the contracts for the Jungle4 Antelope testnet.

Validated network values on `2026-04-04`:

- RPC URL: `https://jungle4.api.eosnation.io`
- chain id: `73e4385a2708e6d7048834fbc1079f2fabb17b3c125b146af438971e90716c4d`
- `/v1/chain/send_transaction2` is available, so `--use-old-rpc` is not required

## Important account constraint

`managementel` and `verification` are not fully account-agnostic in the current codebase:

- `managementel` hardcodes `verification` as the proof contract account
- `verification` hardcodes `managementel` as the only authorized writer

For Jungle4 deployment, create and fund these exact accounts:

- `verification`
- `managementel`

Recommended additional account:

- `dfs`

If you must use different account names, patch the contract constants first and rebuild.

## What you need on Linux

- Debian/Ubuntu-compatible Linux host on `amd64`
- `cleos`
- `cdt-cpp`
- imported keys for the contract accounts in your local wallet
- Jungle4 accounts with enough RAM/CPU/NET

Jungle resources and onboarding:

- account creation and faucet access: `https://jungletestnet.io/`
- monitor, faucet, and PowerUp tools: `https://monitor.jungletestnet.io`

## Install toolchain on Linux

The repository now includes a bootstrap script that installs the required packages from the
official Antelope GitHub releases.

```bash
chmod +x ./scripts/bootstrap-linux-antelope.sh
./scripts/bootstrap-linux-antelope.sh
```

The installer fetches:

- Antelope Leap `.deb` package, which provides `cleos`
- Antelope CDT `.deb` package, which provides `cdt-cpp`

## Build the contracts

```bash
chmod +x ./scripts/build-testnet.sh
./scripts/build-testnet.sh
```

Expected artifacts:

- `dist/verification/verification.wasm`
- `dist/verification/verification.abi`
- `dist/managementel/managementel.wasm`
- `dist/managementel/managementel.abi`
- `dist/dfs/dfs.wasm`
- `dist/dfs/dfs.abi`

## Deploy to Jungle4

The deploy script checks the Jungle4 chain id, verifies that required accounts exist,
builds artifacts by default, deploys contracts, and adds `eosio.code` where needed.

```bash
chmod +x ./scripts/deploy-jungle4.sh
./scripts/deploy-jungle4.sh
```

Defaults:

- `RPC_URL=https://jungle4.api.eosnation.io`
- `VERIFICATION_ACCOUNT=verification`
- `MANAGEMENT_ACCOUNT=managementel`
- `DFS_ACCOUNT=dfs`
- `DEPLOY_DFS=true`
- `BUILD_BEFORE_DEPLOY=true`

Examples:

Deploy only `verification` and `managementel`:

```bash
DEPLOY_DFS=false ./scripts/deploy-jungle4.sh
```

Reuse already built artifacts:

```bash
BUILD_BEFORE_DEPLOY=false ./scripts/deploy-jungle4.sh
```

## Manual deploy commands

If you prefer to deploy manually:

```bash
cleos -u https://jungle4.api.eosnation.io set contract verification ./dist/verification -p verification@active
cleos -u https://jungle4.api.eosnation.io set contract managementel ./dist/managementel -p managementel@active
cleos -u https://jungle4.api.eosnation.io set account permission managementel active --add-code -p managementel@active
cleos -u https://jungle4.api.eosnation.io set contract dfs ./dist/dfs -p dfs@active
cleos -u https://jungle4.api.eosnation.io set account permission dfs active --add-code -p dfs@active
```

`verification` does not need `eosio.code` for the current design.

## Configure `managementel` on Jungle4

Jungle4 `eosio.token` currently exposes `EOS` and `JUNGLE` stats. The examples below use `JUNGLE`
so `setpaytoken` matches a real token symbol on this network.

Configure accepted payments:

```bash
cleos -u https://jungle4.api.eosnation.io push action managementel setpaytoken '[
  "eosio.token",
  "1.0000 JUNGLE",
  "0.1000 JUNGLE"
]' -p managementel@active
```

Enable nonprofit free submissions:

```bash
cleos -u https://jungle4.api.eosnation.io push action managementel setfreecfg '[
  true,
  100
]' -p managementel@active
```

## Optional Jungle4 smoke test

The repository now includes a Jungle4 wrapper around the existing smoke test:

```bash
export OWNER_ACCOUNT=managementel
export MANAGEMENT_ACCOUNT=managementel
export VERIFICATION_ACCOUNT=verification
export RETAIL_ACCOUNT=yourretailacc
export WHOLESALE_ACCOUNT=yourwholesale
export NONPROFIT_ACCOUNT=yournonprofit
chmod +x ./scripts/smoke-test-jungle4.sh
./scripts/smoke-test-jungle4.sh
```

Defaults in the wrapper:

- `RPC_URL=https://jungle4.api.eosnation.io`
- `PAYMENT_TOKEN_CONTRACT=eosio.token`
- `RETAIL_PRICE=1.0000 JUNGLE`
- `WHOLESALE_PRICE=0.1000 JUNGLE`

## Verify on-chain state

```bash
cleos -u https://jungle4.api.eosnation.io get table managementel managementel paytokens
cleos -u https://jungle4.api.eosnation.io get table managementel managementel freepolicy
cleos -u https://jungle4.api.eosnation.io get table verification verification proofs
cleos -u https://jungle4.api.eosnation.io get table dfs dfs pricepolicy
cleos -u https://jungle4.api.eosnation.io get table dfs dfs acpttokens
```

## DFS follow-up

If you deploy `dfs`, finish its policy/token bootstrap before using it for storage receipts.
Use `docs/dfs-testnet-bootstrap.md` for the post-deploy configuration sequence, but replace the
RPC URL with the Jungle4 RPC above.
