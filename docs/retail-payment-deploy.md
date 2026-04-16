# Retail Payment Deploy

This runbook covers deployment of the `verifretpay` contract.

Repository boundary:

- `C:\projects\verification-contract` owns `verif`, `verifbill`, `verifretpay`, and `verifretail`
- `C:\projects\deNotary` owns the off-chain backend
- `C:\projects\decentralized_storage\contracts\dfs` owns the DFS contract

## Purpose

`verifretpay` is the retail payment and authorization contract for:

- accepted retail payment tokens
- exact retail tariffs
- one-time retail usage authorizations consumed by `verif`

It is the target retail payment surface for the unified architecture.

## Build

```bash
./scripts/build-retpay.sh
```

Expected artifacts:

- `dist/verifretpay/verifretpay.wasm`
- `dist/verifretpay/verifretpay.abi`

## deNotary Deploy

```bash
./scripts/deploy-retpay-denotary.sh
```

Defaults:

- `RPC_URL=https://history.denotary.io`
- `RETPAY_ACCOUNT=verifretpay`
- `BUILD_BEFORE_DEPLOY=true`

## Jungle4 Deploy

```bash
./scripts/deploy-retpay-jungle4.sh
```

Defaults:

- `RPC_URL=https://jungle4.api.eosnation.io`
- `RETPAY_ACCOUNT=verifretpay`
- `BUILD_BEFORE_DEPLOY=true`

## Verify

```bash
cleos -u <rpc> get table verifretpay verifretpay rtltokens
cleos -u <rpc> get table verifretpay verifretpay rtltariffs
cleos -u <rpc> get table verifretpay verifretpay rtlauths
```
