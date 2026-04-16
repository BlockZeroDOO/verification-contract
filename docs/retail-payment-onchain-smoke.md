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
export VERIFICATION_OWNER_ACCOUNT=verif
export VERIFICATION_ACCOUNT=verif
export VERIFICATION_BILLING_ACCOUNT=verifbill
export SUBMITTER_ACCOUNT=someuser
```

## Coverage

- token configuration
- tariff configuration
- schema/policy setup on `verif`
- `setauthsrcs` wiring for `verif`
- size-based payment calculation from contract-computed canonical request size
- underpayment rejection
- wrong-token rejection
- exact atomic single transfer
- duplicate request rejection for the same request
- exact atomic batch transfer
- persisted contract-computed `billable_kib` in `verif`
- configured downstream `verif` consumer
