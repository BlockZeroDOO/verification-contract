# Retail Payment On-Chain Smoke Tests

These smoke tests validate the standalone `verifretpay` surface.

## Scripts

- [scripts/smoke-test-retpay.sh](/c:/projects/verification-contract/scripts/smoke-test-retpay.sh:1)
- [scripts/smoke-test-retpay-denotary.sh](/c:/projects/verification-contract/scripts/smoke-test-retpay-denotary.sh:1)
- [scripts/smoke-test-retpay-jungle4.sh](/c:/projects/verification-contract/scripts/smoke-test-retpay-jungle4.sh:1)

## Coverage

- token configuration
- tariff configuration
- schema/policy setup on `verif`
- `setauthsrcs` wiring for `verif`
- size-based payment calculation from `billable_bytes`
- underpayment rejection
- wrong-token rejection
- exact atomic single transfer
- duplicate request rejection for the same request
- exact atomic batch transfer
- persisted `billable_kib` in `verif`
- configured downstream `verif` consumer
