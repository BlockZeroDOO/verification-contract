# Enterprise Billing Deploy

This runbook covers deployment of the `verifbill` contract.

Repository boundary:

- `C:\projects\verification-contract` owns `verif`, `verifretail`, and `verifbill`
- `C:\projects\deNotary` owns the off-chain backend
- `C:\projects\decentralized_storage\contracts\dfs` owns the DFS contract

## Purpose

`verifbill` is the enterprise billing contract for:

- accepted enterprise billing tokens
- subscription plans
- usage packs
- one-time usage authorizations consumed by `verif`

## Build

```bash
./scripts/build-billing.sh
```

Expected artifacts:

- `dist/verifbill/verifbill.wasm`
- `dist/verifbill/verifbill.abi`

## deNotary Deploy

```bash
./scripts/deploy-billing-denotary.sh
```

Defaults:

- `RPC_URL=https://history.denotary.io`
- `BILLING_ACCOUNT=verifbill`
- `BUILD_BEFORE_DEPLOY=true`

## Jungle4 Deploy

```bash
./scripts/deploy-billing-jungle4.sh
```

Defaults:

- `RPC_URL=https://jungle4.api.eosnation.io`
- `BILLING_ACCOUNT=verifbill`
- `BUILD_BEFORE_DEPLOY=true`

## Verify

```bash
cleos -u <rpc> get table verifbill verifbill billtokens
cleos -u <rpc> get table verifbill verifbill plans
cleos -u <rpc> get table verifbill verifbill packs
cleos -u <rpc> get table verifbill verifbill entitlements
cleos -u <rpc> get table verifbill verifbill usageauths
```

## Post-deploy wiring

After deploy, point `verifbill` at the deployed `verif` account that is allowed to consume enterprise usage authorizations:

```bash
cleos -u <rpc> push action verifbill setverifacct '["verif"]' -p verifbill@active
```
