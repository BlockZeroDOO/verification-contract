# deNotary Retail Verification Deploy

This runbook covers deployment of the `verifretail` contract only.

Repository boundary:

- `C:\projects\verification-contract` owns `verifent` and `verifretail`
- `C:\projects\deNotary` owns the off-chain backend
- `C:\projects\decentralized_storage\contracts\dfs` owns the DFS contract

## Purpose

`verifretail` is the wallet-first retail contract that supports atomic on-chain payment plus submit flow.

Retail payment model:

- `token::transfer -> verifretail`
- `verifretail::submit` or `submitroot`
- exact payment only
- no deposit model

## Build

```bash
./scripts/build-retail.sh
```

Expected artifacts:

- `dist/verifretail/verifretail.wasm`
- `dist/verifretail/verifretail.abi`

## deNotary Deploy

```bash
./scripts/deploy-retail-denotary.sh
```

Defaults:

- `RPC_URL=https://history.denotary.io`
- `RETAIL_ACCOUNT=verifretail`
- `BUILD_BEFORE_DEPLOY=true`

## Jungle4 Deploy

```bash
./scripts/deploy-retail-jungle4.sh
```

Defaults:

- `RPC_URL=https://jungle4.api.eosnation.io`
- `RETAIL_ACCOUNT=verifretail`
- `BUILD_BEFORE_DEPLOY=true`

## Verify

```bash
cleos -u <rpc> get table verifretail verifretail rtltokens
cleos -u <rpc> get table verifretail verifretail rtltariffs
cleos -u <rpc> get table verifretail verifretail rtlreceipts
cleos -u <rpc> get table verifretail verifretail commitments
cleos -u <rpc> get table verifretail verifretail batches
```

## Smoke

deNotary:

```bash
export OWNER_ACCOUNT=verifretail
export RETAIL_ACCOUNT=verifretail
export SUBMITTER_ACCOUNT=youruser
./scripts/smoke-test-retail-denotary.sh
```

Jungle4:

```bash
export OWNER_ACCOUNT=verifretail
export RETAIL_ACCOUNT=verifretail
export SUBMITTER_ACCOUNT=youruser
./scripts/smoke-test-retail-jungle4.sh
```
