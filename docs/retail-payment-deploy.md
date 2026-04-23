# Retail Payment Deploy

This runbook covers deployment of the supported retail payment contract `verifretpay`.

Repository boundary:

- `C:\projects\verification-contract` owns `verif`, `verifbill`, and `verifretpay`

## Purpose

`verifretpay` is used for:

- accepted retail tokens
- exact `price_per_kib` tariffs
- atomic retail payment into `verif`

## Build

```bash
./scripts/build-retpay.sh
```

Artifacts:

- `dist/verifretpay/verifretpay.wasm`
- `dist/verifretpay/verifretpay.abi`

## Deploy

deNotary:

```bash
./scripts/deploy-retpay-denotary.sh
```

Jungle4:

```bash
./scripts/deploy-retpay-jungle4.sh
```

Validated Jungle4 retail account:

- `verification` -> `verifretpay`

## Verify

```bash
cleos -u <rpc> get table verification verification rtltokens
cleos -u <rpc> get table verification verification rtltariffs
cleos -u <rpc> get table verification verification retpaycfg
```

## Wiring

```bash
cleos -u <rpc> push action verification setverifacct '["decentrfstor"]' -p verification@active
```
