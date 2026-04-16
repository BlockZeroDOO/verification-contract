# deNotary Verification Deploy

This runbook covers deployment of the enterprise pair:

- `verifbill`
- `verif`

Optional retail companion:

- `verifretpay`

Repository boundary:

- `C:\projects\verification-contract` owns `verif`, `verifbill`, `verifretpay`, and the deprecated compatibility contract `verifretail`
- `C:\projects\deNotary` owns the off-chain backend
- `C:\projects\decentralized_storage\contracts\dfs` owns the DFS contract

## Network values

- RPC URL: `https://history.denotary.io`
- chain id: `9714ab662f0899c3ac4c5a02220f3d7ab61aacae311974239cc75f22c999cc48`

## Requirements

- Linux / WSL host
- `cleos`
- `cdt-cpp`
- imported keys for `verifbill` and `verif`
- deployed `verifbill` and `verif` accounts with enough RAM/CPU/NET

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
./scripts/deploy-billing-denotary.sh
./scripts/deploy-denotary.sh
```

Defaults:

- `RPC_URL=https://history.denotary.io`
- `DENOTARY_CHAIN_ID=9714ab662f0899c3ac4c5a02220f3d7ab61aacae311974239cc75f22c999cc48`
- `BILLING_ACCOUNT=verifbill`
- `VERIFICATION_ACCOUNT=verif`
- `BUILD_BEFORE_DEPLOY=true`

Reuse already built artifacts:

```bash
BUILD_BEFORE_DEPLOY=false ./scripts/deploy-billing-denotary.sh
BUILD_BEFORE_DEPLOY=false ./scripts/deploy-denotary.sh
```

Optional retail payment deploy:

```bash
./scripts/deploy-retpay-denotary.sh
```

## Post-deploy wiring

After deploy, wire the three contracts together:

```bash
cleos -u https://history.denotary.io push action verif setauthsrcs '["verifbill","verifretpay"]' -p verif@active
cleos -u https://history.denotary.io push action verifbill setverifacct '["verif"]' -p verifbill@active
cleos -u https://history.denotary.io push action verifretpay setverifacct '["verif"]' -p verifretpay@active
```

## Manual deploy

```bash
cleos -u https://history.denotary.io set contract verifbill ./dist/verifbill -p verifbill@active
cleos -u https://history.denotary.io set contract verif ./dist/verif -p verif@active
```

Optional retail payment deploy:

```bash
cleos -u https://history.denotary.io set contract verifretpay ./dist/verifretpay -p verifretpay@active
```

`verif` does not require `eosio.code` for the current design.

## Verify

```bash
cleos -u https://history.denotary.io get table verifbill verifbill billtokens
cleos -u https://history.denotary.io get table verifbill verifbill plans
cleos -u https://history.denotary.io get table verifbill verifbill packs
cleos -u https://history.denotary.io get table verifbill verifbill entitlements
cleos -u https://history.denotary.io get table verifbill verifbill usageauths
cleos -u https://history.denotary.io get table verif verif schemas
cleos -u https://history.denotary.io get table verif verif policies
cleos -u https://history.denotary.io get table verif verif commitments
cleos -u https://history.denotary.io get table verif verif batches
```

## Smoke

```bash
export RPC_URL=https://history.denotary.io
export OWNER_ACCOUNT=verif
export BILLING_OWNER_ACCOUNT=verifbill
export VERIFICATION_BILLING_ACCOUNT=verifbill
export VERIFICATION_ACCOUNT=verif
export SUBMITTER_ACCOUNT=youruser
./scripts/smoke-test-onchain.sh
```

Unified retail smoke:

```bash
export VERIFICATION_ACCOUNT=verif
export VERIFICATION_BILLING_ACCOUNT=verifbill
export RETPAY_ACCOUNT=verifretpay
export OWNER_ACCOUNT=verif
export RETPAY_OWNER_ACCOUNT=verifretpay
export SUBMITTER_ACCOUNT=youruser
./scripts/smoke-test-unified-retail.sh
```
