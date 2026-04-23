# Jungle4 Deploy

[BlockZero DOO, Serbia https://blockzero.rs](https://blockzero.rs)
Telegram group: [DeNotaryGroup](https://t.me/DeNotaryGroup)

Supported deploy model on Jungle4:

- `verif`
- `verifbill`
- optional `verifretpay` for retail traffic

Validated Jungle4 account layout:

- `decentrfstor` -> `verif`
- `vadim1111111` -> `verifbill`
- `verification` -> `verifretpay`

## Network

- RPC URL: `https://jungle4.api.eosnation.io`
- chain id: `73e4385a2708e6d7048834fbc1079f2fabb17b3c125b146af438971e90716c4d`

## Build

```bash
./scripts/build-testnet.sh verif
./scripts/build-billing.sh
./scripts/build-retpay.sh
```

## Deploy

```bash
./scripts/deploy-billing-jungle4.sh
./scripts/deploy-jungle4.sh
```

Retail payment companion:

```bash
./scripts/deploy-retpay-jungle4.sh
```

## Wiring

```bash
cleos -u https://jungle4.api.eosnation.io push action vadim1111111 setverifacct '["decentrfstor"]' -p vadim1111111@active
cleos -u https://jungle4.api.eosnation.io push action verification setverifacct '["decentrfstor"]' -p verification@active
```

`verif` no longer exposes a live `setauthsrcs` action.

Production upgrade assumptions:

- existing `schemas` and `policies` rows remain in place
- existing `authsources` configuration remains in place if already set on-chain
- if `authsources` is absent, `verif` defaults to `verifbill` and `verifretpay`
- the current live `authsources` row on Jungle4 is `vadim1111111 / verification`

## Smoke

Enterprise:

```bash
export BILLING_OWNER_ACCOUNT=vadim1111111
export VERIFICATION_BILLING_ACCOUNT=vadim1111111
export VERIFICATION_ACCOUNT=decentrfstor
export SUBMITTER_ACCOUNT=verification
export SCHEMA_ID=1776342316
export POLICY_SINGLE_ID=1776343316
export POLICY_BATCH_ID=1776343317
./scripts/smoke-test-jungle4.sh
```

Retail end-to-end:

```bash
export VERIFICATION_ACCOUNT=decentrfstor
export VERIFICATION_BILLING_ACCOUNT=vadim1111111
export RETPAY_ACCOUNT=verification
export RETPAY_OWNER_ACCOUNT=verification
export SUBMITTER_ACCOUNT=decentrfstor
export SCHEMA_ID=1776342316
export POLICY_SINGLE_ID=1776343316
export POLICY_BATCH_ID=1776343317
./scripts/smoke-test-unified-retail-jungle4.sh
```
