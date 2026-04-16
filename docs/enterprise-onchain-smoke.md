# Enterprise On-Chain Smoke Tests

These smoke tests validate the supported enterprise path:

- `verifbill`
- `verif`

## Scripts

- [scripts/smoke-test-enterprise.sh](/c:/projects/verification-contract/scripts/smoke-test-enterprise.sh:1)
- [scripts/smoke-test-enterprise-denotary.sh](/c:/projects/verification-contract/scripts/smoke-test-enterprise-denotary.sh:1)
- [scripts/smoke-test-enterprise-jungle4.sh](/c:/projects/verification-contract/scripts/smoke-test-enterprise-jungle4.sh:1)

The wrappers delegate to:

- [scripts/smoke-test-onchain.sh](/c:/projects/verification-contract/scripts/smoke-test-onchain.sh:1)

## Coverage

- `addschema`
- minimal `setpolicy`
- `verif::setauthsrcs`
- `verifbill::settoken`
- `verifbill::setpack`
- `verifbill::setverifacct`
- plan or pack funding
- `verifbill::use`
- `verif::submit`
- `verif::submitroot`
- duplicate request rejection
- zero-hash rejection
