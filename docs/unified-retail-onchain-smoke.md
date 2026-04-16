# Unified Retail On-Chain Smoke Tests

## Purpose

These smoke tests validate the full unified retail path:

- `verifretpay` creates one-time retail usage authorization
- `verif` consumes that authorization during `submit`
- `verif` consumes that authorization during `submitroot`
- batch manifest is embedded directly in `submitroot`

Scripts:

- [scripts/smoke-test-unified-retail.sh](/c:/projects/verification-contract/scripts/smoke-test-unified-retail.sh:1)
- [scripts/smoke-test-unified-retail-jungle4.sh](/c:/projects/verification-contract/scripts/smoke-test-unified-retail-jungle4.sh:1)

## Prerequisites

- deployed `verif`
- deployed `verifretpay`
- `cleos`
- `jq`
- imported keys for:
  - `verif` owner account
  - `verifretpay` owner account
  - submitter account used for transfers and submits

## Required env vars

```bash
export RPC_URL=https://your-rpc
export READ_RPC_URL=${RPC_URL}
export VERIFICATION_ACCOUNT=verif
export VERIFICATION_BILLING_ACCOUNT=verifbill
export RETPAY_ACCOUNT=verifretpay
export OWNER_ACCOUNT=verif
export RETPAY_OWNER_ACCOUNT=verifretpay
export SUBMITTER_ACCOUNT=someuser
```

## Run

Generic unified retail smoke:

```bash
./scripts/smoke-test-unified-retail.sh
```

Jungle4:

```bash
./scripts/smoke-test-unified-retail-jungle4.sh
```

## What the unified retail smoke validates

- `verif::setauthsrcs`
- `verifretpay::settoken`
- `verifretpay::setverifacct`
- `verifretpay::setprice`
- `verif::addschema`
- `verif::setpolicy`
- exact retail single authorization through `transfer -> verifretpay`
- `verif::submit` using that authorization
- `verifretpay::consume` triggered by `verif`
- duplicate single request rejection
- exact retail batch authorization through `transfer -> verifretpay`
- `verif::submitroot` using that authorization
- embedded `manifest_hash` in the batch row

## Notes

- this is the target retail path for the unified architecture
- it validates the live interaction between two separate contracts, not just standalone retail payment behavior
