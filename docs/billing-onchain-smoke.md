# Enterprise Billing On-Chain Smoke Tests

## Purpose

These smoke tests validate the current `verifbill` runtime together with the required `verif` wiring for:

- accepted token configuration
- plan configuration
- pack configuration
- entitlement purchase
- atomic enterprise submit
- atomic enterprise batch submit
- contract-computed canonical request size -> `billable_kib` billing
- nearest-expiry entitlement selection

Scripts:

- [scripts/smoke-test-billing.sh](/c:/projects/verification-contract/scripts/smoke-test-billing.sh:1)
- [scripts/smoke-test-billing-denotary.sh](/c:/projects/verification-contract/scripts/smoke-test-billing-denotary.sh:1)
- [scripts/smoke-test-billing-jungle4.sh](/c:/projects/verification-contract/scripts/smoke-test-billing-jungle4.sh:1)

## Prerequisites

- deployed `verifbill` contract
- `cleos`
- `jq`
- imported keys for:
  - billing owner account
  - payer account
  - submitter account
- existing `verif` schema and policy rows for the IDs used by the smoke

## Required env vars

```bash
export RPC_URL=https://your-rpc
export READ_RPC_URL=${RPC_URL}
export BILLING_ACCOUNT=verifbill
export OWNER_ACCOUNT=verifbill
export VERIFICATION_ACCOUNT=verif
export RETAIL_PAYMENT_ACCOUNT=verifretpay
export PAYER_ACCOUNT=somepayer
export SUBMITTER_ACCOUNT=somesubmitter
export SCHEMA_ID=100
export POLICY_SINGLE_ID=200
export POLICY_BATCH_ID=201
export PLAN_INCLUDED_KIB=8
export PACK_INCLUDED_KIB=6
```

## Run

Generic billing smoke:

```bash
./scripts/smoke-test-billing.sh
```

Jungle4:

```bash
export BILLING_ACCOUNT=vadim1111111
export OWNER_ACCOUNT=vadim1111111
export VERIFICATION_ACCOUNT=decentrfstor
export RETAIL_PAYMENT_ACCOUNT=verification
export PAYER_ACCOUNT=verification
export SUBMITTER_ACCOUNT=verification
export SCHEMA_ID=1776342316
export POLICY_SINGLE_ID=1776343316
export POLICY_BATCH_ID=1776343317
./scripts/smoke-test-billing-jungle4.sh
```

deNotary:

```bash
./scripts/smoke-test-billing-denotary.sh
```

## What the billing smoke validates

- `settoken`
- `setplan`
- `setpack`
- plan purchase through `transfer -> verifbill`
- pack purchase through `transfer -> verifbill`
- pre-provisioned schema/policy usage on `verif`
- atomic `submit` for single mode with payer authority
- contract-computed canonical single-request size
- nearest-expiry entitlement selection
- duplicate request rejection
- atomic `submitroot` for batch mode
- contract-computed canonical batch-request size
- stored `billable_kib` matching the computed request size
