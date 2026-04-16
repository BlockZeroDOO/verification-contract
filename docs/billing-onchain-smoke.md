# Enterprise Billing On-Chain Smoke Tests

## Purpose

These smoke tests validate the standalone `verifbill` surface for:

- accepted token configuration
- plan configuration
- pack configuration
- entitlement purchase
- enterprise usage authorization
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
- `use` for single mode
- duplicate request authorization rejection
- `consume`
- `use` for batch mode
