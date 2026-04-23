# Enterprise Billing Deploy

[BlockZero DOO, Serbia https://blockzero.rs](https://blockzero.rs)
Telegram group: [DeNotaryGroup](https://t.me/DeNotaryGroup)

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

Validated Jungle4 billing account:

- `vadim1111111` -> `verifbill`

## Verify

```bash
cleos -u <rpc> get table vadim1111111 vadim1111111 billtokens
cleos -u <rpc> get table vadim1111111 vadim1111111 plans
cleos -u <rpc> get table vadim1111111 vadim1111111 packs
cleos -u <rpc> get table vadim1111111 vadim1111111 entitlements
cleos -u <rpc> get table vadim1111111 vadim1111111 billconfig
```

## Wiring

Point `verifbill` at the deployed `verif` account:

```bash
cleos -u <rpc> push action vadim1111111 setverifacct '["decentrfstor"]' -p vadim1111111@active
```
