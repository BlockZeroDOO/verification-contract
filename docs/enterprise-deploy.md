# deNotary Enterprise Verification Deploy

This runbook covers deployment of the enterprise verification contract surface.

Current contract mapping:

- enterprise contract account: `verifent`
- enterprise WASM target: `verifent`
- implementation wrapper: `verification_enterprise`

Repository boundary:

- `C:\projects\verification-contract` owns `verifent` and `verifretail`
- `C:\projects\deNotary` owns the off-chain backend
- `C:\projects\decentralized_storage\contracts\dfs` owns the DFS contract

## Purpose

The enterprise contract is the billing-agnostic verification surface for:

- KYC-gated access control
- schema and policy governance
- single-record anchoring
- batch anchoring
- commitment and batch lifecycle

It does not support retail token payment flow.

## Build

```bash
./scripts/build-enterprise.sh
```

Expected artifacts:

- `dist/verifent/verifent.wasm`
- `dist/verifent/verifent.abi`

## deNotary Deploy

```bash
./scripts/deploy-enterprise-denotary.sh
```

Defaults:

- `RPC_URL=https://history.denotary.io`
- `VERIFICATION_ACCOUNT=verifent`
- `BUILD_BEFORE_DEPLOY=true`

## Jungle4 Deploy

```bash
./scripts/deploy-enterprise-jungle4.sh
```

Defaults:

- `RPC_URL=https://jungle4.api.eosnation.io`
- `VERIFICATION_ACCOUNT=verifent`
- `BUILD_BEFORE_DEPLOY=true`

## Verify

```bash
cleos -u <rpc> get table verifent verifent kyc
cleos -u <rpc> get table verifent verifent schemas
cleos -u <rpc> get table verifent verifent policies
cleos -u <rpc> get table verifent verifent commitments
cleos -u <rpc> get table verifent verifent batches
```

## Smoke

deNotary:

```bash
export OWNER_ACCOUNT=verifent
export VERIFICATION_ACCOUNT=verifent
export SUBMITTER_ACCOUNT=youruser
./scripts/smoke-test-enterprise-denotary.sh
```

Jungle4:

```bash
export OWNER_ACCOUNT=verifent
export VERIFICATION_ACCOUNT=verifent
export SUBMITTER_ACCOUNT=youruser
./scripts/smoke-test-enterprise-jungle4.sh
```
