# Retail End-to-End On-Chain Smoke Tests

These smoke tests validate the supported retail model:

- `verifretpay` performs atomic retail payment
- `verif` anchors through internal retail entrypoints

## Scripts

- [scripts/smoke-test-unified-retail.sh](/c:/projects/verification-contract/scripts/smoke-test-unified-retail.sh:1)
- [scripts/smoke-test-unified-retail-jungle4.sh](/c:/projects/verification-contract/scripts/smoke-test-unified-retail-jungle4.sh:1)

## Coverage

- `verif::setauthsrcs`
- `verifretpay::settoken`
- `verifretpay::setverifacct`
- `verifretpay::setprice`
- `verif::addschema`
- `verif::setpolicy`
- `transfer -> verifretpay`
- `verif::retailsub`
- `verif::retailbatch`
- persisted `billable_bytes`
- persisted `billable_kib`
- contract-computed canonical request size for single and batch flows
- embedded `manifest_hash`
