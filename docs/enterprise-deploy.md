# deNotary Unified Verification Deploy

This runbook covers deployment of the unified verification contract surface.

Current contract mapping:

- unified anchoring contract account: `verif`
- enterprise billing account: `verifbill`
- unified WASM target: `verif`
- implementation wrapper: `verification_enterprise`

Repository boundary:

- `C:\projects\verification-contract` owns `verif`, `verifretail`, and `verifbill`
- `C:\projects\deNotary` owns the off-chain backend
- `C:\projects\decentralized_storage\contracts\dfs` owns the DFS contract

## Purpose

The unified `verif` contract is the billing-agnostic anchoring surface for:

- KYC-gated access control
- schema and policy governance
- single-record anchoring
- batch anchoring
- commitment and batch lifecycle

It does not support retail token payment flow.

For live enterprise usage it now expects enterprise usage authorization from `verifbill`.

## Build

```bash
./scripts/build-enterprise.sh
```

Expected artifacts:

- `dist/verif/verif.wasm`
- `dist/verif/verif.abi`

## deNotary Deploy

```bash
./scripts/deploy-enterprise-denotary.sh
```

Defaults:

- `RPC_URL=https://history.denotary.io`
- `VERIFICATION_ACCOUNT=verif`
- `BUILD_BEFORE_DEPLOY=true`

## Jungle4 Deploy

```bash
./scripts/deploy-enterprise-jungle4.sh
```

Defaults:

- `RPC_URL=https://jungle4.api.eosnation.io`
- `VERIFICATION_ACCOUNT=verif`
- `BUILD_BEFORE_DEPLOY=true`

## Verify

```bash
cleos -u <rpc> get table verif verif kyc
cleos -u <rpc> get table verif verif schemas
cleos -u <rpc> get table verif verif policies
cleos -u <rpc> get table verif verif commitments
cleos -u <rpc> get table verif verif batches
cleos -u <rpc> get table verifbill verifbill usageauths
```

## Smoke

deNotary:

```bash
export OWNER_ACCOUNT=verif
export BILLING_OWNER_ACCOUNT=verifbill
export VERIFICATION_ACCOUNT=verif
export VERIFICATION_BILLING_ACCOUNT=verifbill
export SUBMITTER_ACCOUNT=youruser
./scripts/smoke-test-enterprise-denotary.sh
```

Jungle4:

```bash
export OWNER_ACCOUNT=verif
export BILLING_OWNER_ACCOUNT=verifbill
export VERIFICATION_ACCOUNT=verif
export VERIFICATION_BILLING_ACCOUNT=verifbill
export SUBMITTER_ACCOUNT=youruser
./scripts/smoke-test-enterprise-jungle4.sh
```
