# Retail Payment On-Chain Smoke Tests

These smoke tests validate the standalone `verifretpay` surface.

## Scripts

- [scripts/smoke-test-retpay.sh](/c:/projects/verification-contract/scripts/smoke-test-retpay.sh:1)
- [scripts/smoke-test-retpay-denotary.sh](/c:/projects/verification-contract/scripts/smoke-test-retpay-denotary.sh:1)
- [scripts/smoke-test-retpay-jungle4.sh](/c:/projects/verification-contract/scripts/smoke-test-retpay-jungle4.sh:1)

## Coverage

- token configuration
- tariff configuration
- size-based payment calculation from `billable_bytes`
- underpayment rejection
- wrong-token rejection
- exact single auth creation
- duplicate auth rejection for the same request
- persisted `billable_kib`
- explicit `consume`
- `cleanauths`
- configured downstream `verif` consumer
