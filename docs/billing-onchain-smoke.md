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

## Required env vars

```bash
export RPC_URL=https://your-rpc
export READ_RPC_URL=${RPC_URL}
export BILLING_ACCOUNT=verifbill
export OWNER_ACCOUNT=verifbill
export VERIFICATION_OWNER_ACCOUNT=verif
export VERIFICATION_ACCOUNT=verif
export RETAIL_PAYMENT_ACCOUNT=verifretpay
export PAYER_ACCOUNT=somepayer
export SUBMITTER_ACCOUNT=somesubmitter
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
- `setauthsrcs` wiring for `verif`
- schema/policy setup on `verif`
- atomic `submit` for single mode with payer authority
- contract-computed canonical single-request size
- nearest-expiry entitlement selection
- duplicate request rejection
- atomic `submitroot` for batch mode
- contract-computed canonical batch-request size
- stored `billable_kib` matching the computed request size
