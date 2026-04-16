# Enterprise Billing On-Chain Smoke Tests

## Purpose

These smoke tests validate the standalone `verifbill` surface for:

- accepted token configuration
- plan configuration
- pack configuration
- entitlement purchase
- enterprise usage authorization
- size-aware `billable_bytes -> billable_kib` authorization binding
- explicit authorization consumption

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
export PAYER_ACCOUNT=somepayer
export SUBMITTER_ACCOUNT=somesubmitter
export PLAN_INCLUDED_KIB=8
export PACK_INCLUDED_KIB=6
export USE_SINGLE_BYTES=1536
export USE_BATCH_BYTES=3072
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
- `use` for single mode with payer authority
- nearest-expiry entitlement selection
- duplicate request authorization rejection
- oversized `billable_bytes` rejection when no single entitlement can satisfy the request
- `consume`
- `cleanauths`
- reissue of the same request after `consume + cleanauths`
- `use` for batch mode
- stored `billable_kib` matching the declared request size

Optional deep expiry coverage:

- set `RUN_EXPIRY_TESTS=true`
- optionally override `AUTH_TTL_WAIT_SEC`
- this enables a long-running check for expired auth cleanup and reissue
