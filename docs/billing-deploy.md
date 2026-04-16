# Enterprise Billing Deploy

This runbook covers deployment of `verifbill`.

Repository boundary:

- `C:\projects\verification-contract` owns `verif`, `verifbill`, and `verifretpay`
- `C:\projects\deNotary` owns the off-chain backend
- `C:\projects\decentralized_storage\contracts\dfs` owns the DFS contract

## Purpose

`verifbill` is the enterprise payment contract for:

- accepted billing tokens
- plans
- packs
- atomic enterprise billing into `verif`

## Build

```bash
./scripts/build-billing.sh
```

Artifacts:

- `dist/verifbill/verifbill.wasm`
- `dist/verifbill/verifbill.abi`

## Deploy

deNotary:

```bash
./scripts/deploy-billing-denotary.sh
```

Jungle4:

```bash
./scripts/deploy-billing-jungle4.sh
```

## Verify

```bash
cleos -u <rpc> get table verifbill verifbill billtokens
cleos -u <rpc> get table verifbill verifbill plans
cleos -u <rpc> get table verifbill verifbill packs
cleos -u <rpc> get table verifbill verifbill entitlements
cleos -u <rpc> get table verifbill verifbill billconfig
```

## Wiring

Point `verifbill` at the deployed `verif` account:

```bash
cleos -u <rpc> push action verifbill setverifacct '["verif"]' -p verifbill@active
```
