# Retail End-to-End On-Chain Smoke Tests

[BlockZero DOO, Serbia https://blockzero.rs](https://blockzero.rs)
Telegram group: [DeNotaryGroup](https://t.me/DeNotaryGroup)

These smoke tests validate the supported retail model:

- `verifretpay` performs atomic retail payment
- `verif` anchors through internal retail entrypoints

## Scripts

- [scripts/smoke-test-unified-retail.sh](/c:/projects/verification-contract/scripts/smoke-test-unified-retail.sh:1)
- [scripts/smoke-test-unified-retail-jungle4.sh](/c:/projects/verification-contract/scripts/smoke-test-unified-retail-jungle4.sh:1)

Latest Jungle4 validated env:

```bash
export VERIFICATION_ACCOUNT=decentrfstor
export VERIFICATION_BILLING_ACCOUNT=vadim1111111
export RETPAY_ACCOUNT=verification
export RETPAY_OWNER_ACCOUNT=verification
export SUBMITTER_ACCOUNT=decentrfstor
export SCHEMA_ID=1776342316
export POLICY_SINGLE_ID=1776343316
export POLICY_BATCH_ID=1776343317
```

## Coverage

- `verifretpay::settoken`
- `verifretpay::setverifacct`
- `verifretpay::setprice`
- pre-provisioned `verif` schema/policy rows
- existing `authsources` row or canonical default caller names
- `transfer -> verifretpay`
- `verif::retailsub`
- `verif::retailbatch`
- persisted `billable_bytes`
- persisted `billable_kib`
- contract-computed canonical request size for single and batch flows
- embedded `manifest_hash`
