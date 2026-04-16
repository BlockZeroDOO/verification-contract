# Retail End-to-End On-Chain Smoke Tests

These smoke tests validate the supported retail model:

- `verifretpay` creates retail authorization
- `verif` consumes that authorization during anchoring

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
- `verif::submit`
- `verif::submitroot`
- downstream `consume`
- embedded `manifest_hash`
