# On-Chain Smoke Tests

Supported smoke coverage:

- enterprise path: `verif + verifbill`
- retail path: `verif + verifretpay`

## Scripts

- [scripts/smoke-test-onchain.sh](/c:/projects/verification-contract/scripts/smoke-test-onchain.sh:1)
- [scripts/smoke-test-enterprise.sh](/c:/projects/verification-contract/scripts/smoke-test-enterprise.sh:1)
- [scripts/smoke-test-billing.sh](/c:/projects/verification-contract/scripts/smoke-test-billing.sh:1)
- [scripts/smoke-test-retpay.sh](/c:/projects/verification-contract/scripts/smoke-test-retpay.sh:1)
- [scripts/smoke-test-unified-retail.sh](/c:/projects/verification-contract/scripts/smoke-test-unified-retail.sh:1)

## Coverage

### Enterprise

- schema and policy setup
- enterprise auth wiring
- billing pack purchase
- `use -> submit -> consume`
- `use -> submitroot -> consume`

### Retail

- retail token and tariff setup
- retail auth creation through `transfer -> verifretpay`
- `verif::submit`
- `verif::submitroot`
- downstream `consume`

## DFS Boundary

DFS smoke is outside this repository:

- `C:\projects\decentralized_storage\contracts\dfs\scripts\smoke-test-dfs.sh`
