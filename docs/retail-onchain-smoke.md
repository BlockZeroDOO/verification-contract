# Retail On-Chain Smoke Tests

## Purpose

These smoke tests validate the retail `atomic pay + submit` path for `verification_retail`.

Scripts:

- [scripts/smoke-test-retail.sh](/c:/projects/verification-contract/scripts/smoke-test-retail.sh:1)
- [scripts/smoke-test-retail-denotary.sh](/c:/projects/verification-contract/scripts/smoke-test-retail-denotary.sh:1)
- [scripts/smoke-test-retail-jungle4.sh](/c:/projects/verification-contract/scripts/smoke-test-retail-jungle4.sh:1)

## Prerequisites

- deployed `verification_retail` contract
- `cleos`
- `jq`
- imported keys for:
  - retail contract owner account
  - submitter/payer account

## Required env vars

```bash
export RPC_URL=https://your-rpc
export READ_RPC_URL=${RPC_URL}
export RETAIL_ACCOUNT=verifretail
export OWNER_ACCOUNT=verifretail
export SUBMITTER_ACCOUNT=someuser
```

Optional:

```bash
export PAYMENT_TOKEN_CONTRACT=eosio.token
export PAYMENT_SYMBOL=EOS
export PRICE_SINGLE="0.0100 EOS"
export PRICE_BATCH="0.0200 EOS"
```

## What the retail smoke validates

- `settoken`
- `setprice` for single and batch
- exact retail single payment
- receipt creation
- single `submit`
- receipt consumption
- duplicate retail single submit rejection without new payment
- exact retail batch payment
- `submitroot`
- batch receipt consumption
- underpayment rejection
- wrong-token rejection

## Notes

- the retail flow is wallet-first and does not require a trusted backend
- for Jungle4, using a separate `READ_RPC_URL` for table polling is recommended
- recommended Jungle4 read endpoint: `https://jungle4.cryptolions.io`
- the current retail memo format is:

```text
single|submitter|external_ref_hex
batch|submitter|external_ref_hex
```

- current implementation requires `payer == submitter`
