# Retail Payment On-Chain Smoke Tests

These smoke tests validate the current `verifretpay` runtime together with the required `verif` wiring.

## Scripts

- [scripts/smoke-test-retpay.sh](/c:/projects/verification-contract/scripts/smoke-test-retpay.sh:1)
- [scripts/smoke-test-retpay-denotary.sh](/c:/projects/verification-contract/scripts/smoke-test-retpay-denotary.sh:1)
- [scripts/smoke-test-retpay-jungle4.sh](/c:/projects/verification-contract/scripts/smoke-test-retpay-jungle4.sh:1)

## Required env vars

```bash
export RPC_URL=https://your-rpc
export READ_RPC_URL=${RPC_URL}
export RETPAY_ACCOUNT=verifretpay
export OWNER_ACCOUNT=verifretpay
export VERIFICATION_ACCOUNT=verif
export VERIFICATION_BILLING_ACCOUNT=verifbill
export SUBMITTER_ACCOUNT=someuser
export SCHEMA_ID=100
export POLICY_SINGLE_ID=200
export POLICY_BATCH_ID=201
```

Latest Jungle4 validated env:

```bash
export RETPAY_ACCOUNT=verification
export OWNER_ACCOUNT=verification
export VERIFICATION_ACCOUNT=decentrfstor
export VERIFICATION_BILLING_ACCOUNT=vadim1111111
export SUBMITTER_ACCOUNT=decentrfstor
export SCHEMA_ID=1776342316
export POLICY_SINGLE_ID=1776343316
export POLICY_BATCH_ID=1776343317
```

## Coverage

- token configuration
- tariff configuration
- pre-provisioned schema/policy usage on `verif`
- size-based payment calculation from contract-computed canonical request size
- underpayment rejection
- wrong-token rejection
- exact atomic single transfer
- duplicate request rejection for the same request
- exact atomic batch transfer
- persisted contract-computed `billable_kib` in `verif`
- configured downstream `verif` consumer
