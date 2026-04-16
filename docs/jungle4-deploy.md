# Jungle4 Verification Deploy

This runbook covers deployment of the enterprise pair on Jungle4:

- `verifbill`
- `verif`

Optional retail companion:

- `verifretpay`

Repository boundary:

- `C:\projects\verification-contract` owns `verif`, `verifbill`, `verifretpay`, and the deprecated compatibility contract `verifretail`
- `C:\projects\deNotary` owns the off-chain backend
- `C:\projects\decentralized_storage\contracts\dfs` owns the DFS contract

## Network values

- RPC URL: `https://jungle4.api.eosnation.io`
- chain id: `73e4385a2708e6d7048834fbc1079f2fabb17b3c125b146af438971e90716c4d`

## Requirements

- Linux / WSL host
- `cleos`
- `cdt-cpp`
- imported keys for `verifbill` and `verif`
- deployed Jungle4 `verifbill` and `verif` accounts with enough RAM/CPU/NET

## Build

```bash
./scripts/build-testnet.sh
```

Expected artifacts:

- `dist/verifbill/verifbill.wasm`
- `dist/verifbill/verifbill.abi`
- `dist/verif/verif.wasm`
- `dist/verif/verif.abi`

## Deploy

```bash
./scripts/deploy-billing-jungle4.sh
./scripts/deploy-jungle4.sh
```

Optional retail payment deploy:

```bash
./scripts/deploy-retpay-jungle4.sh
```

## Post-deploy wiring

After deploy, wire the three contracts together:

```bash
cleos -u https://jungle4.api.eosnation.io push action verif setauthsrcs '["verifbill","verifretpay"]' -p verif@active
cleos -u https://jungle4.api.eosnation.io push action verifbill setverifacct '["verif"]' -p verifbill@active
cleos -u https://jungle4.api.eosnation.io push action verifretpay setverifacct '["verif"]' -p verifretpay@active
```

Defaults:

- `RPC_URL=https://jungle4.api.eosnation.io`
- `BILLING_ACCOUNT=verifbill`
- `VERIFICATION_ACCOUNT=verif`
- `BUILD_BEFORE_DEPLOY=true`

## Manual deploy

```bash
cleos -u https://jungle4.api.eosnation.io set contract verifbill ./dist/verifbill -p verifbill@active
cleos -u https://jungle4.api.eosnation.io set contract verif ./dist/verif -p verif@active
```

Optional retail payment deploy:

```bash
cleos -u https://jungle4.api.eosnation.io set contract verifretpay ./dist/verifretpay -p verifretpay@active
```

## Verify

```bash
cleos -u https://jungle4.api.eosnation.io get table verifbill verifbill billtokens
cleos -u https://jungle4.api.eosnation.io get table verifbill verifbill plans
cleos -u https://jungle4.api.eosnation.io get table verifbill verifbill packs
cleos -u https://jungle4.api.eosnation.io get table verifbill verifbill entitlements
cleos -u https://jungle4.api.eosnation.io get table verifbill verifbill usageauths
cleos -u https://jungle4.api.eosnation.io get table verif verif schemas
cleos -u https://jungle4.api.eosnation.io get table verif verif policies
cleos -u https://jungle4.api.eosnation.io get table verif verif commitments
cleos -u https://jungle4.api.eosnation.io get table verif verif batches
```

## Smoke

```bash
export OWNER_ACCOUNT=verif
export BILLING_OWNER_ACCOUNT=verifbill
export VERIFICATION_BILLING_ACCOUNT=verifbill
export VERIFICATION_ACCOUNT=verif
export SUBMITTER_ACCOUNT=youruser
./scripts/smoke-test-jungle4.sh
```

Unified retail smoke:

```bash
export VERIFICATION_ACCOUNT=verif
export VERIFICATION_BILLING_ACCOUNT=verifbill
export RETPAY_ACCOUNT=verifretpay
export OWNER_ACCOUNT=verif
export RETPAY_OWNER_ACCOUNT=verifretpay
export SUBMITTER_ACCOUNT=youruser
./scripts/smoke-test-unified-retail-jungle4.sh
```
