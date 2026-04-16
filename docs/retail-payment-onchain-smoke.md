# Retail Payment On-Chain Smoke Tests

## Purpose

These smoke tests validate the standalone `verifretpay` surface for:

- accepted token configuration
- exact tariff configuration
- underpayment rejection
- wrong-token rejection
- retail authorization creation
- duplicate authorization rejection for the same request
- explicit authorization consumption

Scripts:

- [scripts/smoke-test-retpay.sh](/c:/projects/verification-contract/scripts/smoke-test-retpay.sh:1)
- [scripts/smoke-test-retpay-denotary.sh](/c:/projects/verification-contract/scripts/smoke-test-retpay-denotary.sh:1)
- [scripts/smoke-test-retpay-jungle4.sh](/c:/projects/verification-contract/scripts/smoke-test-retpay-jungle4.sh:1)

## Prerequisites

- deployed `verifretpay` contract
- `cleos`
- `jq`
- imported keys for:
  - retail payment owner account
  - submitter account used for transfers

## Required env vars

```bash
export RPC_URL=https://your-rpc
export READ_RPC_URL=${RPC_URL}
export RETPAY_ACCOUNT=verifretpay
export OWNER_ACCOUNT=verifretpay
export SUBMITTER_ACCOUNT=someuser
```

## Run

Generic retail payment smoke:

```bash
./scripts/smoke-test-retpay.sh
```

Jungle4:

```bash
./scripts/smoke-test-retpay-jungle4.sh
```

deNotary:

```bash
./scripts/smoke-test-retpay-denotary.sh
```

## What the retail payment smoke validates

- `settoken`
- `setprice`
- underpayment reject
- wrong-token reject
- exact single retail authorization
- duplicate request rejection
- `consume`
- exact batch retail authorization
