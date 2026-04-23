# deNotary Deploy

Supported deploy model on deNotary:

- `verif`
- `verifbill`
- optional `verifretpay` for retail traffic

## Network

- RPC URL: `https://history.denotary.io`
- chain id: `9714ab662f0899c3ac4c5a02220f3d7ab61aacae311974239cc75f22c999cc48`

## Build

```bash
./scripts/build-testnet.sh verif
./scripts/build-billing.sh
./scripts/build-retpay.sh
```

## Deploy

```bash
./scripts/deploy-billing-denotary.sh
./scripts/deploy-denotary.sh
```

Retail payment companion:

```bash
./scripts/deploy-retpay-denotary.sh
```

## Wiring

```bash
cleos -u https://history.denotary.io push action verifbill setverifacct '["verif"]' -p verifbill@active
cleos -u https://history.denotary.io push action verifretpay setverifacct '["verif"]' -p verifretpay@active
```

`verif` no longer exposes a live `setauthsrcs` action.

Production upgrade assumptions:

- existing `schemas` and `policies` rows remain in place
- existing `authsources` configuration remains in place if already set on-chain
- if `authsources` is absent, `verif` defaults to `verifbill` and `verifretpay`

## Smoke

Enterprise:

```bash
export RPC_URL=https://history.denotary.io
export BILLING_OWNER_ACCOUNT=verifbill
export VERIFICATION_BILLING_ACCOUNT=verifbill
export VERIFICATION_ACCOUNT=verif
export SUBMITTER_ACCOUNT=youruser
export SCHEMA_ID=100
export POLICY_SINGLE_ID=200
export POLICY_BATCH_ID=201
./scripts/smoke-test-onchain.sh
```

Retail end-to-end:

```bash
export VERIFICATION_ACCOUNT=verif
export VERIFICATION_BILLING_ACCOUNT=verifbill
export RETPAY_ACCOUNT=verifretpay
export RETPAY_OWNER_ACCOUNT=verifretpay
export SUBMITTER_ACCOUNT=youruser
export SCHEMA_ID=100
export POLICY_SINGLE_ID=200
export POLICY_BATCH_ID=201
./scripts/smoke-test-unified-retail.sh
```
